import os
import json
import uuid
import logging
from typing import List, Optional, Tuple, AsyncGenerator
from backend.app.core.config import settings
from backend.app.schemas.document import DocumentMetadata, DocumentChunk
from backend.app.schemas.chat import Citation, ChatResponse
from backend.app.services.ingestion.extractor import extract_text_from_pdf, extract_text_from_docx
from backend.app.services.ingestion.chunker import process_and_chunk_document
from backend.app.services.embeddings.sentence_transformer import SentenceTransformerEmbeddingService
from backend.app.services.retrieval.chroma_store import ChromaVectorStore
from backend.app.services.generation.llm_factory import get_llm_service
from backend.app.services.language.detector import detect_language
from datetime import datetime

logger = logging.getLogger(__name__)

class RAGService:
    _instance = None

    def __init__(self):
        self.embedding_service = SentenceTransformerEmbeddingService()
        self.vector_store = ChromaVectorStore()
        self.llm_service = get_llm_service()
        self.registry_file = os.path.join(settings.BASE_DIR, "data", "documents_registry.json")
        self.documents_metadata = self._load_persisted_metadata()

    def _load_persisted_metadata(self) -> dict:
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {k: DocumentMetadata(**v) for k, v in data.items()}
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

    def process_file(self, file_path: str, original_filename: str) -> DocumentMetadata:
        doc_id = str(uuid.uuid4())[:8]
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
            chunk_overlap=settings.CHUNK_OVERLAP
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

    def list_documents(self) -> List[DocumentMetadata]:
        return list(self.documents_metadata.values())

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        return self.documents_metadata.get(document_id)

    def delete_document(self, document_id: str) -> bool:
        if document_id in self.documents_metadata:
            meta = self.documents_metadata[document_id]
            self.vector_store.delete_document(document_id)
            
            # Clean up local file if present
            file_path = os.path.join(settings.UPLOAD_DIR, meta.filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                    
            del self.documents_metadata[document_id]
            self._save_persisted_metadata()
            return True
        return False

    async def answer_query(
        self,
        query: str,
        document_id: Optional[str] = None,
        target_language: str = "auto"
    ) -> Tuple[str, List[Citation], str, str]:
        # 1. Detect query language
        detected_lang = detect_language(query)
        
        # 2. Resolve target response language
        final_lang = detected_lang if target_language == "auto" else target_language
        if final_lang not in ["en", "hi", "hinglish"]:
            final_lang = "en"

        # 3. Embed query using multilingual embedding
        query_vector = self.embedding_service.embed_query(query)

        # 4. Search in ChromaDB
        citations = self.vector_store.search(
            query_embedding=query_vector,
            top_k=settings.TOP_K,
            document_id=document_id
        )

        # Filter by similarity threshold if citations are too distant
        relevant_citations = [
            c for c in citations if c.similarity_score >= settings.SIMILARITY_THRESHOLD
        ]
        
        # If none pass threshold, fall back to top 1 if available or empty
        if not relevant_citations and citations and citations[0].similarity_score > 0.2:
            relevant_citations = [citations[0]]

        # 5. LLM Grounded Generation
        answer = await self.llm_service.generate_response(
            query=query,
            context_chunks=relevant_citations,
            target_language=final_lang
        )

        return answer, relevant_citations, detected_lang, final_lang

    async def stream_query(
        self,
        query: str,
        document_id: Optional[str] = None,
        target_language: str = "auto"
    ) -> Tuple[AsyncGenerator[str, None], List[Citation], str, str]:
        detected_lang = detect_language(query)
        final_lang = detected_lang if target_language == "auto" else target_language
        if final_lang not in ["en", "hi", "hinglish"]:
            final_lang = "en"

        query_vector = self.embedding_service.embed_query(query)
        citations = self.vector_store.search(
            query_embedding=query_vector,
            top_k=settings.TOP_K,
            document_id=document_id
        )
        relevant_citations = [
            c for c in citations if c.similarity_score >= settings.SIMILARITY_THRESHOLD
        ]
        if not relevant_citations and citations and citations[0].similarity_score > 0.2:
            relevant_citations = [citations[0]]

        stream_gen = self.llm_service.generate_stream(
            query=query,
            context_chunks=relevant_citations,
            target_language=final_lang
        )
        return stream_gen, relevant_citations, detected_lang, final_lang
