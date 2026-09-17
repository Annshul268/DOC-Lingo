from pydantic import BaseModel, Field
from typing import Optional, List
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
    conversation_id: Optional[str] = Field(None, description="Optional conversation session ID")

class Citation(BaseModel):
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    text_snippet: str
    similarity_score: float

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    detected_language: str
    target_language: str
    document_id: Optional[str] = None
