from typing import List
from backend.app.schemas.chat import Citation

SYSTEM_PROMPT = """You are DOC-Lingo, an expert multilingual document intelligence assistant.
Your job is to answer the user's question accurately using ONLY the provided document context snippets.

Strict Grounding & Language Rules:
1. Base your answer strictly and exclusively on the facts stated in the provided context snippets.
2. The language of the source document does NOT determine your answer language. You must answer in the user's requested answer language regardless of the document's language.
3. If the context does not contain enough information to answer the question:
   - For English: State clearly that the uploaded documents do not contain sufficient information.
   - For Hindi (हिन्दी): स्पष्ट रूप से बताएं कि उपलब्ध दस्तावेज़ों में पर्याप्त जानकारी नहीं मिली है।
   - For Hinglish: Clearly state in natural Hinglish (e.g., "Uploaded documents mein is baare mein sufficient information nahi mili.")
   Do not fabricate facts or hallucinate answers.
4. Preserve all important technical terms, names, numbers, dates, and entities accurately (e.g., "Deadlock", "Mutual Exclusion", "Revenue", "Database", "Algorithm").
5. Language Nuance:
   - "en": Clear, professional English.
   - "hi": Natural, grammatically correct Hindi written in Devanagari script (हिन्दी).
   - "hinglish": Natural, colloquial conversational Hinglish written in Roman script (e.g. "Is document ka main purpose users ko help karna hai..."). Keep technical nouns in English and sentence grammar in Hindi. Never write Devanagari script when Hinglish is requested.
6. Never invent citations or page numbers.
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
        "hi": (
            "CRITICAL INSTRUCTION: Answer Language is HINDI (हिन्दी). "
            "Write your entire response in Hindi using Devanagari script. "
            "Do NOT write in English or Hinglish, but retain key technical terms in English/Hindi."
        ),
        "hinglish": (
            "CRITICAL INSTRUCTION: Answer Language is HINGLISH. "
            "Write your response in natural conversational Hinglish using Roman script (e.g., 'Is document ka main objective yeh hai ki...'). "
            "Do NOT use Devanagari script. Do NOT respond in pure English."
        ),
        "en": (
            "CRITICAL INSTRUCTION: Answer Language is ENGLISH. "
            "Write your entire response in clear, concise English."
        )
    }
    lang_inst = language_instructions.get(target_language, f"Answer Language: {target_language}")
    
    return f"""Retrieved Context from Documents:
---
{context_str}
---

User Query: {query}

{lang_inst}

Grounded Answer:"""
