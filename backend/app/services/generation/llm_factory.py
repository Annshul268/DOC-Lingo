import json
import re
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
    def _no_context_message(self, query: str, target_language: str) -> str:
        years = re.findall(r'\b(19\d\d|20\d\d)\b', query)
        year_str = f" {years[0]}" if years else ""
        if target_language == "hi":
            if year_str:
                return f"दिए गए दस्तावेज़ में{year_str} के लिए पर्याप्त जानकारी नहीं मिली।"
            return "दिए गए दस्तावेज़ों में इस प्रश्न के लिए पर्याप्त जानकारी नहीं मिली।"
        elif target_language == "hinglish":
            if year_str:
                return f"Provided document mein{year_str} ke baare mein information nahi mili."
            return "Provided documents mein is question ke liye sufficient information nahi mili."
        else:
            if year_str:
                return f"I couldn't find information for{year_str} in the provided document."
            return "I could not find sufficient information to answer this question in the provided documents."

    def _extract_concise_fact(self, query: str, snippet: str) -> tuple:
        """
        Generically extracts the most relevant factual sentence from a chunk for factual questions.
        Returns (concise_text, has_factual_match)
        """
        query_years = set(re.findall(r'\b(19\d\d|20\d\d)\b', query))
        query_words = set(re.findall(r'[a-zA-Z0-9\u0900-\u097F]+', query.lower())) - {
            'what', 'was', 'is', 'are', 'were', 'the', 'in', 'on', 'at', 'of', 'for', 'to',
            'a', 'an', 'and', 'or', 'how', 'many', 'much', 'did', 'does', 'do', 'which',
            'kya', 'hai', 'hain', 'tha', 'thi', 'the', 'ka', 'ki', 'ke', 'ko', 'me', 'mein',
            'se', 'par', 'aur', 'ya', 'kitna', 'kitne', 'kitni', 'kab', 'tak', 'this', 'that'
        }

        # Normalize currency font artifacts (e.g. 'I84 crore' -> '₹84 crore')
        snippet = re.sub(r'(?<=\s)[I■](?=\d+\s*(?:crore|lakh|thousand|million|billion|\b))', '₹', snippet)

        # Normalize text flow (un-wrap soft line breaks within sentences)
        lines_raw = [l.strip() for l in snippet.split('\n') if l.strip()]
        merged_lines = []
        for l in lines_raw:
            if not merged_lines:
                merged_lines.append(l)
                continue
            prev = merged_lines[-1]
            is_prev_heading = (len(prev) < 50 and not prev.endswith(','))
            is_bullet = bool(re.match(r'^(\d+[\.\)]|\-|\*|•)\s+', l))
            if prev.endswith(('.', '!', '?', '।', ':')) or is_prev_heading or is_bullet:
                merged_lines.append(l)
            else:
                merged_lines[-1] = prev + ' ' + l
        normalized_snippet = '\n'.join(merged_lines)

        # 1. Temporal conflict check (e.g. asking for 2026 when snippet only has 2025)
        if query_years:
            snippet_years = set(re.findall(r'\b(19\d\d|20\d\d)\b', normalized_snippet))
            if snippet_years and not query_years.intersection(snippet_years):
                return None, False

        # 2. Split snippet into genuine sentences preserving unbroken flow
        sentences = [s.strip() for s in re.split(r'(?<=[.?!।])\s+', normalized_snippet) if s.strip()]
        factual_sentences = [s for s in sentences if not s.endswith('?') and s.count('?') == 0]
        if not factual_sentences:
            factual_sentences = sentences

        # Exclude common query stop words and generic words from sentence matching
        from backend.app.services.retrieval.reranker import GenericRAGReranker
        from backend.app.services.language.translator import devanagari_to_roman

        content_query_words = {w for w in query_words if w not in GenericRAGReranker.GENERIC_WORDS and len(w) > 2}
        expanded_query_words = set(content_query_words)
        for w in list(content_query_words):
            roman = devanagari_to_roman(w).lower()
            if roman and len(roman) > 2:
                expanded_query_words.add(roman)
            for syn in GenericRAGReranker.CROSS_LINGUAL_SYNONYMS.get(w, []):
                expanded_query_words.add(syn.lower())

        scored_sentences = []
        for idx, s in enumerate(factual_sentences):
            s_lower = s.lower()
            score = 0.0
            for w in expanded_query_words:
                if re.search(r'\b' + re.escape(w) + r'\b', s_lower):
                    score += 2.0
                    if w in GenericRAGReranker.CROSS_LINGUAL_SYNONYMS:
                        score += 3.0
            for y in query_years:
                if y in s:
                    score += 3.0
            if re.search(r'\b\d+\b', s):
                score += 0.5

            has_pred = any(re.search(r'\b' + re.escape(p) + r'\b', s_lower) for p in GenericRAGReranker.EXPLANATORY_PREDICATES)
            is_list = any(re.search(r'\b' + re.escape(m) + r'\b', s_lower) for m in GenericRAGReranker.LIST_MARKERS)

            if has_pred:
                score += 2.0
            if is_list and not has_pred:
                score -= 2.5
            if len(s) < 50 and not s.endswith(('.', '!', '?', '।')) and not has_pred:
                score -= 3.5

            scored_sentences.append((score, idx, s))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        if scored_sentences and scored_sentences[0][0] >= 1.5:
            top_score, top_idx, top_sent = scored_sentences[0]

            # If adjacent sentence in the same snippet provides continuing explanation, include it
            result_sents = [top_sent]
            if top_idx + 1 < len(factual_sentences):
                next_s = factual_sentences[top_idx + 1]
                next_lower = next_s.lower()
                next_has_pred = any(re.search(r'\b' + re.escape(p) + r'\b', next_lower) for p in GenericRAGReranker.EXPLANATORY_PREDICATES)
                next_matches_kw = any(w in next_lower for w in expanded_query_words)
                if next_has_pred and (next_matches_kw or len(factual_sentences) <= 3) and not next_s.endswith('?'):
                    result_sents.append(next_s)

            combined_fact = ' '.join(result_sents)
            # Remove any solitary heading lines or header/footer artifacts
            combined_fact = re.sub(r'^[A-Za-z0-9\s—–•]+\s*[—–•]\s*Page\s*\d+\s*', '', combined_fact)
            combined_fact = re.sub(r'^[—–•]\s*[A-Za-z0-9\s,]+(?:\n|$)', '', combined_fact)
            combined_fact = re.sub(r'^(?:[A-Za-z\s]{2,30}:)\s*', '', combined_fact)
            lines = [l.strip() for l in combined_fact.split('\n') if l.strip()]
            if len(lines) > 1 and len(lines[0]) < 50 and not lines[0].endswith(('.', '!', '?')):
                lines = lines[1:]
            clean_fact = ' '.join(lines)
            return clean_fact.strip(), True

        # If no content words matched at all, there is no grounded answer
        if content_query_words and scored_sentences and scored_sentences[0][0] < 1.0:
            return None, False

        return snippet, True

    async def generate_response(self, query: str, context_chunks: List[Citation], target_language: str) -> str:
        if not context_chunks:
            return self._no_context_message(query, target_language)

        top_chunk = context_chunks[0]
        snippet = top_chunk.text_snippet.strip()
        
        concise_fact, has_match = self._extract_concise_fact(query, snippet)
        if not has_match or not concise_fact:
            return self._no_context_message(query, target_language)

        translated_body = translate_text(concise_fact, target_language)

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
        if not self.api_key or "YOUR_GEMINI_API_KEY" in self.api_key:
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
    has_gemini_key = bool(settings.GEMINI_API_KEY and "YOUR_GEMINI_API" not in settings.GEMINI_API_KEY)
    if (provider == "gemini" or provider not in ("ollama", "mock")) and has_gemini_key:
        return GeminiLLMService()
    elif provider == "ollama":
        return OllamaLLMService()
    elif provider == "mock":
        return MockLLMService()
    else:
        return MockLLMService()
