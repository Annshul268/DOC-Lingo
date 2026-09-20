import os
import logging
from backend.app.core.config import settings
from backend.app.services.embeddings.base import BaseEmbeddingService
from backend.app.services.embeddings.sentence_transformer import SentenceTransformerEmbeddingService
from backend.app.services.embeddings.gemini import GeminiEmbeddingService

logger = logging.getLogger(__name__)

def get_embedding_service() -> BaseEmbeddingService:
    provider = getattr(settings, "EMBEDDING_PROVIDER", "auto").lower()

    if provider == "gemini":
        logger.info("Initializing Gemini Embedding Service (text-embedding-004)...")
        return GeminiEmbeddingService()
    
    if provider == "sentence-transformers":
        logger.info("Initializing SentenceTransformer Embedding Service...")
        return SentenceTransformerEmbeddingService()

    # 'auto' mode:
    # Check if running in a cloud/containerized environment (Render, Heroku, etc.)
    # Render sets RENDER=true. In memory-constrained cloud environments (512MB limit),
    # Gemini embeddings avoid the ~500MB PyTorch model download and prevent OOM kills.
    is_cloud = (
        os.environ.get("RENDER", "").lower() in ("true", "1")
        or getattr(settings, "APP_ENV", "").lower() == "production"
    )
    has_gemini_key = bool(
        settings.GEMINI_API_KEY 
        and settings.GEMINI_API_KEY.strip() 
        and "YOUR_GEMINI_API_KEY" not in settings.GEMINI_API_KEY
    )

    if is_cloud and has_gemini_key:
        logger.info("Auto-selected Gemini Embedding Service for cloud deployment to conserve memory.")
        return GeminiEmbeddingService()

    # Local development & testing default: SentenceTransformers
    logger.info("Auto-selected SentenceTransformer Embedding Service for local environment.")
    return SentenceTransformerEmbeddingService()
