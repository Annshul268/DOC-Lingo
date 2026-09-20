import os
import shutil
import json
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse
from backend.app.core.config import settings
from backend.app.schemas.document import DocumentUploadResponse, DocumentListResponse, DocumentMetadata
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.rag_service import RAGService
from backend.app.services.ingestion.extractor import sanitize_filename

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_provider": settings.LLM_PROVIDER
    }

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    # 1. Validate file extension
    original_filename = sanitize_filename(file.filename or "unknown_file")
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {settings.ALLOWED_EXTENSIONS}"
        )

    # 2. Save locally and validate size
    temp_path = os.path.join(settings.UPLOAD_DIR, original_filename)
    try:
        contents = await file.read()
        if len(contents) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds limit of {settings.MAX_FILE_SIZE_MB}MB."
            )
        with open(temp_path, "wb") as f:
            f.write(contents)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # 3. Process and ingest
    try:
        rag = RAGService.get_instance()
        meta = rag.process_file(temp_path, original_filename)
        return DocumentUploadResponse(
            document_id=meta.document_id,
            filename=meta.filename,
            page_count=meta.page_count,
            chunk_count=meta.chunk_count,
            status=meta.status,
            message=f"Document successfully indexed into {meta.chunk_count} chunks."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error indexing document: {str(e)}"
        )

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    rag = RAGService.get_instance()
    docs = rag.list_documents()
    return DocumentListResponse(documents=docs, total=len(docs))

@router.get("/documents/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: str):
    rag = RAGService.get_instance()
    doc = rag.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc

@router.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    rag = RAGService.get_instance()
    doc = rag.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")
        
    return FileResponse(
        path=file_path,
        filename=doc.filename,
        media_type="application/octet-stream"
    )

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    rag = RAGService.get_instance()
    success = rag.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"message": "Document deleted successfully", "document_id": document_id}

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    rag = RAGService.get_instance()
    answer, citations, detected_lang, target_lang = await rag.answer_query(
        query=request.query,
        document_id=request.document_id,
        target_language=request.target_language.value if request.target_language else "auto"
    )
    return ChatResponse(
        answer=answer,
        citations=citations,
        detected_language=detected_lang,
        target_language=target_lang,
        document_id=request.document_id
    )

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    rag = RAGService.get_instance()
    stream_gen, citations, detected_lang, target_lang = await rag.stream_query(
        query=request.query,
        document_id=request.document_id,
        target_language=request.target_language.value if request.target_language else "auto"
    )
    
    async def sse_generator():
        # First send citations event
        citations_data = [c.model_dump() for c in citations]
        init_payload = {
            "type": "meta",
            "detected_language": detected_lang,
            "target_language": target_lang,
            "citations": citations_data
        }
        yield f"data: {json.dumps(init_payload)}\n\n"
        
        # Stream answer chunks
        async for token in stream_gen:
            chunk_payload = {"type": "token", "token": token}
            yield f"data: {json.dumps(chunk_payload)}\n\n"
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
