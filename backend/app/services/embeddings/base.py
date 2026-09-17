from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of document chunk strings."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate an embedding for a user query."""
        pass
