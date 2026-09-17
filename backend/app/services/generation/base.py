from abc import ABC, abstractmethod
from typing import List, AsyncGenerator
from backend.app.schemas.chat import Citation

class BaseLLMService(ABC):
    @abstractmethod
    async def generate_response(
        self,
        query: str,
        context_chunks: List[Citation],
        target_language: str
    ) -> str:
        """Generate a grounded response using retrieved context chunks."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        query: str,
        context_chunks: List[Citation],
        target_language: str
    ) -> AsyncGenerator[str, None]:
        """Stream generated response tokens."""
        pass
