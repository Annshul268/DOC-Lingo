import os
import json
import uuid
import shutil
import logging
from typing import List, Optional, Tuple, AsyncGenerator
from backend.app.core.config import settings
from backend.app.schemas.document import DocumentMetadata, DocumentChunk
from backend.app.schemas.chat import Citation, ChatResponse
from backend.app.services.ingestion.extractor import extract_text_from_pdf, extract_text_from_docx
from backend.app.services.ingestion.chunker import process_and_chunk_document
from backend.app.services.embeddings.factory import get_embedding_service
from backend.app.services.retrieval.chroma_store import ChromaVectorStore
from backend.app.services.retrieval.reranker import GenericRAGReranker
from backend.app.services.generation.llm_factory import get_llm_service
from backend.app.services.language.detector import detect_language
from datetime import datetime

logger = logging.getLogger(__name__)

class RAGService:
    _instance = None

    def __init__(self):
        self.embedding_service = get_embedding_service()
        is_gemini = self.embedding_service.__class__.__name__ == "GeminiEmbeddingService"
        collection_name = f"{settings.COLLECTION_NAME}_gemini" if is_gemini else settings.COLLECTION_NAME
        self.vector_store = ChromaVectorStore(collection_name=collection_name)
        self.reranker = GenericRAGReranker()
        self.llm_service = get_llm_service()
        self.registry_file = os.path.join(settings.BASE_DIR, "data", "documents_registry.json")
        self.documents_metadata = self._load_persisted_metadata()
        self._reconcile_with_vector_store()

    def _reconcile_with_vector_store(self) -> None:
        """
        Reconciles in-memory and persisted metadata with the underlying ChromaDB vector store.
        Ensures document IDs, chunk counts, page counts, and user_id always match indexed vectors.
        """
        try:
            chroma_data = self.vector_store.collection.get(include=["metadatas"])
            if not chroma_data or not chroma_data.get("metadatas"):
                return

            chroma_docs = {}
            for m in chroma_data["metadatas"]:
                did = m.get("document_id")
                fname = m.get("filename")
                pnum = m.get("page_number", 1)
                lang = m.get("language", "en")
                uid = m.get("user_id", "legacy_unassigned")
                if not did or not fname:
                    continue
                if did not in chroma_docs:
                    chroma_docs[did] = {
                        "filename": fname,
                        "pages": set(),
                        "chunk_count": 0,
                        "language": lang,
                        "user_id": uid
                    }
                chroma_docs[did]["pages"].add(pnum)
                chroma_docs[did]["chunk_count"] += 1

            existing_by_fname = {meta.filename: meta for meta in self.documents_metadata.values()}
            changed = False

            for did, info in chroma_docs.items():
                fname = info["filename"]
                uid = info["user_id"]
                if did in self.documents_metadata:
                    meta = self.documents_metadata[did]
                    if meta.chunk_count != info["chunk_count"]:
                        meta.chunk_count = info["chunk_count"]
                        changed = True
                    if not getattr(meta, "user_id", None):
                        meta.user_id = uid
                        changed = True
                elif fname in existing_by_fname:
                    old_meta = existing_by_fname[fname]
                    if old_meta.document_id in self.documents_metadata:
                        del self.documents_metadata[old_meta.document_id]
                    new_meta = DocumentMetadata(
                        document_id=did,
                        user_id=uid or getattr(old_meta, "user_id", "legacy_unassigned"),
                        filename=fname,
                        file_type=old_meta.file_type,
                        file_size_bytes=old_meta.file_size_bytes,
                        page_count=max(old_meta.page_count, len(info["pages"])),
                        chunk_count=info["chunk_count"],
                        uploaded_at=old_meta.uploaded_at,
                        status="indexed",
                        language=info["language"]
                    )
                    self.documents_metadata[did] = new_meta
                    changed = True
                else:
                    ext = os.path.splitext(fname)[1].lower().replace(".", "").upper()
                    file_path = os.path.join(settings.UPLOAD_DIR, uid, did, fname)
                    if not os.path.exists(file_path):
                        file_path = os.path.join(settings.UPLOAD_DIR, fname)
                    fsize = os.path.getsize(file_path) if os.path.exists(file_path) else 1024
                    new_meta = DocumentMetadata(
                        document_id=did,
                        user_id=uid,
                        filename=fname,
                        file_type=ext or "PDF",
                        file_size_bytes=fsize,
                        page_count=len(info["pages"]) or 1,
                        chunk_count=info["chunk_count"],
                        uploaded_at=datetime.utcnow(),
                        status="indexed",
                        language=info["language"]
                    )
                    self.documents_metadata[did] = new_meta
                    changed = True

            for did in list(self.documents_metadata.keys()):
                if did not in chroma_docs:
                    del self.documents_metadata[did]
                    changed = True

            if changed:
                self._save_persisted_metadata()
                logger.info(f"Reconciled documents registry with ChromaDB: {list(self.documents_metadata.keys())}")
        except Exception as e:
            logger.warning(f"Error during vector store metadata reconciliation: {e}")

    def _load_persisted_metadata(self) -> dict:
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    res = {}
                    for k, v in data.items():
                        if "user_id" not in v or not v["user_id"]:
                            v["user_id"] = "legacy_unassigned"
                        res[k] = DocumentMetadata(**v)
                    return res
            except Exception as e:
                logger.warning(f"Could not load documents_registry.json: {e}")
                return {}
        return {}

    def _save_persisted_metadata(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(
                    {k: v.model_dump(mode="json") for k, v in self.documents_metadata.items()},
                    f,
                    indent=2,
                    default=str
                )
        except Exception as e:
            logger.error(f"Failed to save documents_registry.json: {e}")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RAGService()
        return cls._instance

    def process_file(
        self,
        file_path: str,
        original_filename: str,
        user_id: str = "default_user",
        document_id: Optional[str] = None
    ) -> DocumentMetadata:
        # If a document with the same filename already exists FOR THIS USER, remove its old chunks
        for old_id, old_meta in list(self.documents_metadata.items()):
            if old_meta.user_id == user_id and old_meta.filename == original_filename:
                self.vector_store.delete_document(old_id, user_id=user_id)
                del self.documents_metadata[old_id]

        doc_id = document_id or str(uuid.uuid4())[:8]
        file_ext = os.path.splitext(original_filename)[1].lower()
        file_size = os.path.getsize(file_path)

        # 1. Extraction
        if file_ext == ".pdf":
            pages_data = extract_text_from_pdf(file_path)
        elif file_ext == ".docx":
            pages_data = extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {file_ext}")

        page_count = len(pages_data) if pages_data else 1
        
        # 2. Chunking
        chunks = process_and_chunk_document(
            document_id=doc_id,
            filename=original_filename,
            pages_data=pages_data,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            user_id=user_id
        )

        # Detect primary language of document from sample chunks
        detected_doc_lang = "en"
        if chunks:
            sample_text = " ".join([c.text for c in chunks[:3]])
            detected_doc_lang = detect_language(sample_text)

        # 3. Multilingual Embedding
        if chunks:
            chunk_texts = [c.text for c in chunks]
            embeddings = self.embedding_service.embed_documents(chunk_texts)
            # 4. Vector Storage
            self.vector_store.add_chunks(chunks, embeddings)

        meta = DocumentMetadata(
            document_id=doc_id,
            user_id=user_id,
            filename=original_filename,
            file_type=file_ext.replace(".", "").upper(),
            file_size_bytes=file_size,
            page_count=page_count,
            chunk_count=len(chunks),
            uploaded_at=datetime.utcnow(),
            status="indexed",
            language=detected_doc_lang
        )
        self.documents_metadata[doc_id] = meta
        self._save_persisted_metadata()
        return meta

    def list_documents(self, user_id: str = "default_user") -> List[DocumentMetadata]:
        self._reconcile_with_vector_store()
        return [doc for doc in self.documents_metadata.values() if doc.user_id == user_id]

    def get_document(self, document_id: str, user_id: str = "default_user") -> Optional[DocumentMetadata]:
        doc = self.documents_metadata.get(document_id)
        if not doc or doc.user_id != user_id:
            return None
        return doc

    def delete_document(self, document_id: str, user_id: str = "default_user") -> bool:
        if document_id in self.documents_metadata:
            meta = self.documents_metadata[document_id]
            if meta.user_id != user_id:
                logger.warning(f"Unauthorized deletion attempt for document {document_id} by user {user_id}")
                return False

            self.vector_store.delete_document(document_id, user_id=user_id)
            
            # Clean up user's isolated local directory if present
            user_doc_dir = os.path.join(settings.UPLOAD_DIR, user_id, document_id)
            if os.path.exists(user_doc_dir):
                try:
                    shutil.rmtree(user_doc_dir, ignore_errors=True)
                except Exception:
                    pass

            # Legacy file cleanup
            flat_file = os.path.join(settings.UPLOAD_DIR, meta.filename)
            if os.path.exists(flat_file):
                try:
                    os.remove(flat_file)
                except Exception:
                    pass
                    
            del self.documents_metadata[document_id]
            self._save_persisted_metadata()
            return True
        return False



    def _enrich_candidates_with_context(self, candidates: List[Citation]) -> List[Citation]:
        """Enriches short candidate chunks or isolated headings with adjacent paragraph context from the same document and page."""
        enriched = []
        for c in candidates:
            if len(c.text_snippet.strip()) < 120 and c.chunk_index is not None and c.document_id:
                next_c = self.vector_store.get_chunk(c.document_id, c.chunk_index + 1)
                if next_c and next_c.page_number == c.page_number:
                    combined_text = f"{c.text_snippet.strip()}\n\n{next_c.text_snippet.strip()}"
                    enriched.append(Citation(
                        document_id=c.document_id,
                        filename=c.filename,
                        page_number=c.page_number,
                        chunk_index=c.chunk_index,
                        text_snippet=combined_text,
                        similarity_score=c.similarity_score
                    ))
                    continue
            enriched.append(c)
        return enriched

    async def answer_query(
        self,
        query: str,
        user_id: str = "default_user",
        document_id: Optional[str] = None,
        target_language: str = "auto",
        response_style: str = "explain"
    ) -> Tuple[str, List[Citation], str, str]:
        # 1. Detect query language
        detected_lang = detect_language(query)
        
        # 2. Resolve target response language
        final_lang = detected_lang if target_language == "auto" else target_language
        if final_lang not in ["en", "hi", "hinglish"]:
            final_lang = "en"

        # 3. Ownership check if specific document requested
        if document_id:
            doc = self.get_document(document_id, user_id=user_id)
            if not doc:
                logger.warning(f"User '{user_id}' requested query against unauthorized/nonexistent doc '{document_id}'")
                return (
                    "The requested document was not found in your workspace.",
                    [],
                    detected_lang,
                    final_lang
                )

        # 4. Embed query using multilingual embedding
        query_vector = self.embedding_service.embed_query(query)

        # 5. Search candidate pool in ChromaDB strictly within this user's scope
        candidate_k = getattr(settings, "RETRIEVAL_K", 16)
        candidates = self.vector_store.search(
            query_embedding=query_vector,
            top_k=candidate_k,
            user_id=user_id,
            document_id=document_id
        )

        logger.info(f"=== RAG QUERY: '{query}' [User: {user_id}] [Lang: {detected_lang} -> {final_lang}] [Style: {response_style}] ===")
        logger.info(f"Retrieved {len(candidates)} candidate chunks from ChromaDB (pool size {candidate_k})")
        for idx, c in enumerate(candidates[:6], 1):
            logger.debug(f"  Candidate {idx}: P{c.page_number} C{c.chunk_index} [Score: {c.similarity_score:.4f}] Sec: {c.section_heading} | Text: {repr(c.text_snippet[:80])}")

        # 6. Rerank candidates using intent-aware multi-factor scoring
        final_k = getattr(settings, "FINAL_CONTEXT_K", settings.TOP_K)
        relevant_citations = self.reranker.rerank(
            query=query,
            citations=candidates,
            top_k=final_k
        )

        logger.info(f"Selected {len(relevant_citations)} final evidence chunks after reranking (target max {final_k}):")
        for idx, c in enumerate(relevant_citations, 1):
            logger.info(f"  Selected {idx}: P{c.page_number} C{c.chunk_index} [Score: {c.similarity_score:.4f}] Sec: {c.section_heading} | Text: {repr(c.text_snippet[:100])}")

        # 7. LLM Grounded Generation
        answer = await self.llm_service.generate_response(
            query=query,
            context_chunks=relevant_citations,
            target_language=final_lang,
            response_style=response_style
        )

        # Clear citations if the generated answer indicates information was not found
        not_found_markers = [
            "could not find", "couldn't find", "not find", "no information",
            "not contain", "does not contain", "not mentioned",
            "पर्याप्त जानकारी नहीं मिली", "जानकारी नहीं", "information nahi mili", "nahi mila"
        ]
        if any(marker in answer.lower() for marker in not_found_markers):
            relevant_citations = []

        return answer, relevant_citations, detected_lang, final_lang

    async def stream_query(
        self,
        query: str,
        user_id: str = "default_user",
        document_id: Optional[str] = None,
        target_language: str = "auto",
        response_style: str = "explain"
    ) -> Tuple[AsyncGenerator[str, None], List[Citation], str, str]:
        detected_lang = detect_language(query)
        final_lang = detected_lang if target_language == "auto" else target_language
        if final_lang not in ["en", "hi", "hinglish"]:
            final_lang = "en"

        if document_id:
            doc = self.get_document(document_id, user_id=user_id)
            if not doc:
                async def empty_stream():
                    yield "The requested document was not found in your workspace."
                return empty_stream(), [], detected_lang, final_lang

        query_vector = self.embedding_service.embed_query(query)
        candidate_k = getattr(settings, "RETRIEVAL_K", 16)
        candidates = self.vector_store.search(
            query_embedding=query_vector,
            top_k=candidate_k,
            user_id=user_id,
            document_id=document_id
        )

        final_k = getattr(settings, "FINAL_CONTEXT_K", settings.TOP_K)
        relevant_citations = self.reranker.rerank(
            query=query,
            citations=candidates,
            top_k=final_k
        )

        stream_gen = self.llm_service.generate_stream(
            query=query,
            context_chunks=relevant_citations,
            target_language=final_lang,
            response_style=response_style
        )
        return stream_gen, relevant_citations, detected_lang, final_lang
