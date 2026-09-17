from typing import List
from backend.app.schemas.chat import Citation

SYSTEM_PROMPT = """You are DOC-Lingo, an expert multilingual document intelligence assistant.
Your job is to answer the user's question accurately using ONLY the provided document context snippets.

Strict Grounding Rules:
1. Base your answer strictly and exclusively on the facts stated in the provided context snippets.
2. If the context does not contain enough information to answer the question, state clearly in the target language that the uploaded documents do not contain this information. Do not fabricate facts.
3. Preserve all crucial technical terms (e.g., "Deadlock", "Mutual Exclusion", "Thread", "Semaphore", "Database", "Index").
4. Never invent or hallucinate citations or page numbers.
5. Answer in the requested target language:
   - "en": Clear and concise English.
   - "hi": Natural Hindi (Devanagari script: हिन्दी).
   - "hinglish": Natural, colloquial Hinglish (Hindi written using the Roman English alphabet, e.g. "Deadlock tab hota hai jab multiple processes ek doosre ka wait karte hain...").
6. Provide structured, easy-to-read answers with bullet points or paragraphs where appropriate.
"""

def build_context_block(citations: List[Citation]) -> str:
    """Formats retrieved citations into a readable numbered context block."""
    if not citations:
        return "No relevant context found in documents."
        
    blocks = []
    for idx, citation in enumerate(citations, 1):
        blocks.append(
            f"[Source {idx}] (File: {citation.filename}, Page: {citation.page_number})\n{citation.text_snippet}"
        )
    return "\n\n".join(blocks)

def build_user_prompt(query: str, citations: List[Citation], target_language: str) -> str:
    context_str = build_context_block(citations)
    
    language_instructions = {
        "hi": "Target Language: Hindi (Devanagari script: हिन्दी). Give your full answer in Hindi while preserving key technical terms.",
        "hinglish": "Target Language: Hinglish (Hindi in Roman script). Give your full answer in conversational Hinglish (e.g., 'Deadlock ek aisi condition hai jisme...'). Keep technical words in English.",
        "en": "Target Language: English. Give your full answer in clear English."
    }
    lang_inst = language_instructions.get(target_language, f"Target Language: {target_language}")
    
    return f"""Retrieved Context:
---
{context_str}
---

User Question: {query}
{lang_inst}

Grounded Answer:"""
