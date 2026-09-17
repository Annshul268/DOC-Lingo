from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from backend.app.schemas.document import DocumentChunk
from backend.app.schemas.chat import Citation

class BaseVectorStore(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        """Add chunks and corresponding vectors to the store."""
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        document_id: Optional[str] = None
    ) -> List[Citation]:
        """Perform semantic search and return relevant chunks as Citations."""
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        """Remove all vectors associated with a document_id."""
        pass

    @abstractmethod
    def list_document_ids(self) -> List[str]:
        """List distinct document IDs present in the store."""
        pass
