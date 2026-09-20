import logging
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.core.config import settings
from backend.app.schemas.document import DocumentChunk
from backend.app.schemas.chat import Citation
from backend.app.services.retrieval.vector_store import BaseVectorStore

logger = logging.getLogger(__name__)

class ChromaVectorStore(BaseVectorStore):
    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.COLLECTION_NAME
        
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        if not chunks:
            return
            
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "language": chunk.language or "en"
            }
            for chunk in chunks
        ]
        
        # Batch insert to stay within Chroma limitations
        batch_size = 200
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            self.collection.upsert(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end]
            )
        logger.info(f"Successfully stored {len(chunks)} chunks in ChromaDB collection '{self.collection_name}'.")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        document_id: Optional[str] = None
    ) -> List[Citation]:
        where_filter = None
        if document_id:
            where_filter = {"document_id": document_id}
            
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Resilient fallback: if document_id was provided but returned 0 results (e.g. ID desync),
        # query without filter so available documents can still answer the question
        if document_id and (not results or not results.get("ids") or not results["ids"][0]):
            logger.warning(f"No chunks found with filter document_id='{document_id}', querying across available documents.")
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

        citations: List[Citation] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return citations
            
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i] if (results.get("metadatas") and results["metadatas"][0]) else None
            if not meta:
                continue
            text = results["documents"][0][i] if (results.get("documents") and results["documents"][0]) else ""
            distance = results["distances"][0][i] if (results.get("distances") and results["distances"][0]) else 0.0
            # For cosine distance in chromadb, similarity = 1 - distance
            similarity = max(0.0, 1.0 - distance)
            
            citations.append(
                Citation(
                    document_id=meta.get("document_id", ""),
                    filename=meta.get("filename", ""),
                    page_number=int(meta.get("page_number", 1)),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    text_snippet=text,
                    similarity_score=round(float(similarity), 4)
                )
            )
            
        return citations

    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})
        logger.info(f"Deleted vectors for document {document_id}")

    def list_document_ids(self) -> List[str]:
        # Fetch metadata to see distinct document ids
        results = self.collection.get(include=["metadatas"])
        if not results or not results.get("metadatas"):
            return []
        ids = set(m["document_id"] for m in results["metadatas"] if "document_id" in m)
        return list(ids)

    def get_chunk(self, document_id: str, chunk_index: int) -> Optional[Citation]:
        try:
            results = self.collection.get(
                where={"$and": [{"document_id": document_id}, {"chunk_index": chunk_index}]},
                include=["documents", "metadatas"]
            )
            if results and results.get("ids") and len(results["ids"]) > 0:
                meta = results["metadatas"][0]
                text = results["documents"][0]
                return Citation(
                    document_id=meta["document_id"],
                    filename=meta["filename"],
                    page_number=int(meta["page_number"]),
                    chunk_index=int(meta["chunk_index"]),
                    text_snippet=text,
                    similarity_score=1.0
                )
        except Exception as e:
            logger.debug(f"Could not retrieve chunk {chunk_index} for document {document_id}: {e}")
        return None
