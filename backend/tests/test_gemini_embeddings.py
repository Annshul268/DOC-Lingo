import pytest
from unittest.mock import patch, MagicMock
from backend.app.core.config import settings
from backend.app.services.embeddings.gemini import GeminiEmbeddingService
from backend.app.services.embeddings.sentence_transformer import SentenceTransformerEmbeddingService
from backend.app.services.embeddings.factory import get_embedding_service

def test_embedding_factory_selection():
    import os
    # When no key is set and provider is auto
    with patch.object(settings, "GEMINI_API_KEY", ""):
        with patch.object(settings, "EMBEDDING_PROVIDER", "auto"):
            svc = get_embedding_service()
            assert isinstance(svc, SentenceTransformerEmbeddingService)

    # When gemini key is configured and cloud env is detected (RENDER=true)
    with patch.dict(os.environ, {"RENDER": "true"}):
        with patch.object(settings, "GEMINI_API_KEY", "AIzaSyTestKey123"):
            with patch.object(settings, "EMBEDDING_PROVIDER", "auto"):
                svc = get_embedding_service()
                assert isinstance(svc, GeminiEmbeddingService)

    # When provider is explicitly gemini
    with patch.object(settings, "EMBEDDING_PROVIDER", "gemini"):
        svc = get_embedding_service()
        assert isinstance(svc, GeminiEmbeddingService)

    # When provider is explicitly sentence-transformers
    with patch.object(settings, "EMBEDDING_PROVIDER", "sentence-transformers"):
        svc = get_embedding_service()
        assert isinstance(svc, SentenceTransformerEmbeddingService)

def test_gemini_embedding_query():
    gemini_svc = GeminiEmbeddingService(api_key="fake-key")
    fake_vector = [0.1] * 768

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "embedding": {
            "values": fake_vector
        }
    }

    with patch("httpx.Client.post", return_value=mock_response):
        res = gemini_svc.embed_query("test query")
        assert len(res) == 768
        assert res[0] == 0.1

def test_gemini_embedding_documents_batch():
    gemini_svc = GeminiEmbeddingService(api_key="fake-key")
    fake_vector_1 = [0.1] * 768
    fake_vector_2 = [0.2] * 768

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "embeddings": [
            {"values": fake_vector_1},
            {"values": fake_vector_2}
        ]
    }

    with patch("httpx.Client.post", return_value=mock_response):
        res = gemini_svc.embed_documents(["chunk 1", "chunk 2"])
        assert len(res) == 2
        assert len(res[0]) == 768
        assert res[0][0] == 0.1
        assert res[1][0] == 0.2
