from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Any
from enum import Enum

class LanguageChoice(str, Enum):
    AUTO = "auto"
    ENGLISH = "en"
    HINDI = "hi"
    HINGLISH = "hinglish"

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The user question in English, Hindi, or Hinglish")
    document_id: Optional[str] = Field(None, description="Optional document ID filter. None means all documents.")
    target_language: Optional[LanguageChoice] = Field(LanguageChoice.AUTO, description="Target answer language")
    language: Optional[str] = Field(None, description="Alias for target_language")
    conversation_id: Optional[str] = Field(None, description="Optional conversation session ID")

    @model_validator(mode="before")
    @classmethod
    def resolve_language_alias(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # Normalize language or target_language
            lang = values.get("language") or values.get("target_language")
            if lang:
                lang_str = str(lang).lower().strip()
                mapping = {
                    "english": LanguageChoice.ENGLISH,
                    "en": LanguageChoice.ENGLISH,
                    "hindi": LanguageChoice.HINDI,
                    "hi": LanguageChoice.HINDI,
                    "hinglish": LanguageChoice.HINGLISH,
                    "auto": LanguageChoice.AUTO,
                }
                values["target_language"] = mapping.get(lang_str, LanguageChoice.AUTO)
        return values

class Citation(BaseModel):
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    text_snippet: str
    similarity_score: float
    section_heading: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    detected_language: str
    target_language: str
    language: Optional[str] = None
    sources: Optional[List[Citation]] = None
    document_id: Optional[str] = None

    @model_validator(mode="after")
    def populate_aliases(self):
        if not self.language:
            self.language = self.target_language
        if not self.sources:
            self.sources = self.citations
        return self
