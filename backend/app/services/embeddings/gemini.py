import logging
from typing import List
import httpx
from backend.app.core.config import settings
from backend.app.services.embeddings.base import BaseEmbeddingService

logger = logging.getLogger(__name__)

class GeminiEmbeddingService(BaseEmbeddingService):
    """
    Google Gemini Embedding API service using text-embedding-004.
    Runs via lightweight HTTP calls, requiring ~0 MB of local memory,
    making it ideal for memory-constrained cloud environments (e.g. Render Free 512 MB).
    """
    def __init__(self, api_key: str = None, model: str = "text-embedding-004"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def embed_query(self, text: str) -> List[float]:
        if not text or not text.strip():
            text = "empty query"
            
        url = f"{self.base_url}/{self.model}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{self.model}",
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    embedding = data.get("embedding", {}).get("values", [])
                    if embedding:
                        return embedding
                logger.error(f"Gemini embed_query failed with status {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Gemini embed_query error: {e}")

        # Return dummy zero-vector with standard 768 dimensions on failure so pipeline doesn't crash
        return [0.0] * 768

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        clean_texts = [t if (t and t.strip()) else " " for t in texts]
        url = f"{self.base_url}/{self.model}:batchEmbedContents?key={self.api_key}"
        
        all_embeddings: List[List[float]] = []
        batch_size = 50  # Batch up to 50 chunks per API call

        with httpx.Client(timeout=60.0) as client:
            for i in range(0, len(clean_texts), batch_size):
                batch = clean_texts[i:i + batch_size]
                requests_payload = [
                    {
                        "model": f"models/{self.model}",
                        "content": {
                            "parts": [{"text": chunk}]
                        }
                    }
                    for chunk in batch
                ]
                
                try:
                    res = client.post(url, json={"requests": requests_payload})
                    if res.status_code == 200:
                        data = res.json()
                        embeddings_data = data.get("embeddings", [])
                        for emb_entry in embeddings_data:
                            all_embeddings.append(emb_entry.get("values", [0.0] * 768))
                    else:
                        logger.error(f"Gemini batchEmbedContents failed ({res.status_code}): {res.text}")
                        # Fallback for failed batch
                        for _ in batch:
                            all_embeddings.append([0.0] * 768)
                except Exception as e:
                    logger.error(f"Gemini embed_documents exception: {e}")
                    for _ in batch:
                        all_embeddings.append([0.0] * 768)

        return all_embeddings
