import re
from typing import List, Dict, Any
from backend.app.schemas.document import DocumentChunk
from backend.app.services.language.detector import detect_language

def split_text_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks of roughly `chunk_size` characters, respecting sentence boundaries.
    """
    if not text:
        return []
        
    # Split text by sentence boundaries (supports English periods, Hindi purna viram ।)
    sentences = re.split(r'(?<=[.?!।\n])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_len = len(sentence)
        if current_length + sentence_len > chunk_size and current_chunk:
            chunk_str = " ".join(current_chunk)
            chunks.append(chunk_str)
            
            # Create overlap
            overlap_sentences = []
            overlap_len = 0
            for s in reversed(current_chunk):
                if overlap_len + len(s) <= chunk_overlap:
                    overlap_sentences.insert(0, s)
                    overlap_len += len(s)
                else:
                    break
            current_chunk = overlap_sentences
            current_length = overlap_len
            
        current_chunk.append(sentence)
        current_length += sentence_len
        
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

def process_and_chunk_document(
    document_id: str,
    filename: str,
    pages_data: List[Dict[str, Any]],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[DocumentChunk]:
    """
    Converts page-level extracted data into granular, page-aware DocumentChunks.
    """
    all_chunks: List[DocumentChunk] = []
    global_chunk_idx = 0
    
    for page_info in pages_data:
        page_num = page_info["page_number"]
        page_text = page_info["text"]
        
        chunks = split_text_into_chunks(page_text, chunk_size, chunk_overlap)
        for chunk_text in chunks:
            lang = detect_language(chunk_text)
            chunk_obj = DocumentChunk(
                chunk_id=f"{document_id}_p{page_num}_c{global_chunk_idx}",
                document_id=document_id,
                filename=filename,
                page_number=page_num,
                chunk_index=global_chunk_idx,
                text=chunk_text,
                language=lang
            )
            all_chunks.append(chunk_obj)
            global_chunk_idx += 1
            
    return all_chunks
