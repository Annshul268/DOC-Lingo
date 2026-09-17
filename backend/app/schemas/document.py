from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    language: Optional[str] = "en"

class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    uploaded_at: datetime
    status: str = "indexed"  # uploading, processing, extracting, embedding, indexed, error
    error_message: Optional[str] = None
    language: Optional[str] = "unknown"

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    status: str
    message: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]
    total: int
