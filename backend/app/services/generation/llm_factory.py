import json
import logging
from typing import List, AsyncGenerator
import httpx
from backend.app.core.config import settings
from backend.app.schemas.chat import Citation
from backend.app.services.generation.base import BaseLLMService
from backend.app.services.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.app.services.language.translator import translate_text

logger = logging.getLogger(__name__)

class MockLLMService(BaseLLMService):
    """
    Fallback mock service for environments without Ollama or external keys.
    Generates grounded answers based directly on extracted context chunks in the requested language.
    """
    async def generate_response(self, query: str, context_chunks: List[Citation], target_language: str) -> str:
        if not context_chunks:
            if target_language == "hi":
                return "दिए गए दस्तावेज़ों में इस प्रश्न के लिए पर्याप्त जानकारी नहीं मिली।"
            elif target_language == "hinglish":
                return "Provided documents mein is question ke liye sufficient information nahi mili."
            else:
                return "I could not find sufficient information to answer this question in the provided documents."

        top_chunk = context_chunks[0]
        snippet = top_chunk.text_snippet.strip()
        translated_body = translate_text(snippet, target_language)
        
        if target_language == "hi":
            return f"दस्तावेज़ '{top_chunk.filename}' (पृष्ठ {top_chunk.page_number}) के अनुसार:\n\n{translated_body}"
        elif target_language == "hinglish":
            return f"Document '{top_chunk.filename}' (Page {top_chunk.page_number}) ke mutaabiq:\n\n{translated_body}"
        else:
            return f"According to '{top_chunk.filename}' (Page {top_chunk.page_number}):\n\n{translated_body}"

    async def generate_stream(self, query: str, context_chunks: List[Citation], target_language: str) -> AsyncGenerator[str, None]:
        full_text = await self.generate_response(query, context_chunks, target_language)
        words = full_text.split(" ")
        for w in words:
            yield w + " "

class GeminiLLMService(BaseLLMService):
    """
    Google Gemini API LLM service (free tier available via AI Studio).
    """
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self.fallback = MockLLMService()

    async def generate_response(self, query: str, context_chunks: List[Citation], target_language: str) -> str:
        if not self.api_key:
            return await self.fallback.generate_response(query, context_chunks, target_language)
        prompt = build_user_prompt(query, context_chunks, target_language)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.2}
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                logger.warning(f"Gemini API returned status {res.status_code}. Falling back to local synthesizer.")
                return await self.fallback.generate_response(query, context_chunks, target_language)
        except Exception as e:
            logger.warning(f"Gemini request failed ({e}). Falling back to local synthesizer.")
            return await self.fallback.generate_response(query, context_chunks, target_language)

    async def generate_stream(self, query: str, context_chunks: List[Citation], target_language: str) -> AsyncGenerator[str, None]:
        full_text = await self.generate_response(query, context_chunks, target_language)
        for w in full_text.split(" "):
            yield w + " "

class OllamaLLMService(BaseLLMService):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.fallback = MockLLMService()

    async def generate_response(self, query: str, context_chunks: List[Citation], target_language: str) -> str:
        prompt = build_user_prompt(query, context_chunks, target_language)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": SYSTEM_PROMPT,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.2}
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    return data.get("response", "").strip()
                else:
                    logger.warning(f"Ollama returned {res.status_code}, falling back to mock synthesizer.")
                    return await self.fallback.generate_response(query, context_chunks, target_language)
        except Exception as e:
            logger.warning(f"Failed to connect to Ollama at {self.base_url} ({e}). Falling back to local synthesizer.")
            return await self.fallback.generate_response(query, context_chunks, target_language)

    async def generate_stream(self, query: str, context_chunks: List[Citation], target_language: str) -> AsyncGenerator[str, None]:
        prompt = build_user_prompt(query, context_chunks, target_language)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": SYSTEM_PROMPT,
                        "prompt": prompt,
                        "stream": True,
                        "options": {"temperature": 0.2}
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                data = json.loads(line)
                                token = data.get("response", "")
                                yield token
                                if data.get("done", False):
                                    break
                    else:
                        async for token in self.fallback.generate_stream(query, context_chunks, target_language):
                            yield token
        except Exception as e:
            logger.warning(f"Ollama stream failed ({e}), falling back to local stream.")
            async for token in self.fallback.generate_stream(query, context_chunks, target_language):
                yield token

def get_llm_service() -> BaseLLMService:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "gemini" or (settings.GEMINI_API_KEY and provider not in ("ollama", "mock")):
        return GeminiLLMService()
    elif provider == "ollama":
        return OllamaLLMService()
    elif provider == "mock":
        return MockLLMService()
    else:
        return OllamaLLMService()
