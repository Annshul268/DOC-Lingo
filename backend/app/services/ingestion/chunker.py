import re
from typing import List, Dict, Any
from backend.app.schemas.document import DocumentChunk
from backend.app.services.language.detector import detect_language

def split_text_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into coherent chunks respecting paragraph units, headings, and sentence boundaries.
    Avoids unnecessarily combining unrelated sections.
    """
    if not text or not text.strip():
        return []

    # 1. Normalize line breaks
    normalized = re.sub(r'\r\n|\r', '\n', text).strip()
    raw_blocks = [b.strip() for b in re.split(r'\n\s*\n', normalized) if b.strip()]
    if not raw_blocks:
        raw_blocks = [normalized]

    # 2. Attach standalone headings to the following paragraph
    blocks = []
    pending_header = ""
    for b in raw_blocks:
        is_heading = (
            len(b) < 70 and
            not b.endswith(('.', '?', '!', '।', ';')) and
            not b.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*'))
        )
        if is_heading:
            if pending_header:
                pending_header += "\n" + b
            else:
                pending_header = b
            continue

        if pending_header:
            combined = f"{pending_header}\n{b}"
            pending_header = ""
        else:
            combined = b
        blocks.append(combined)

    if pending_header:
        if blocks:
            blocks[-1] = f"{blocks[-1]}\n{pending_header}"
        else:
            blocks.append(pending_header)

    # 3. Form chunks preserving semantic boundaries
    chunks = []
    current_chunk = []
    current_len = 0

    for block in blocks:
        block_len = len(block)
        if block_len > chunk_size:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            # Split oversized block along genuine sentence boundaries
            sentences = re.split(r'(?<=[.?!।])\s+', block)
            curr_sent = []
            curr_sent_len = 0
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                if curr_sent_len + len(s) > chunk_size and curr_sent:
                    chunks.append(" ".join(curr_sent))
                    overlap_s = []
                    overlap_len = 0
                    for prev_s in reversed(curr_sent):
                        if overlap_len + len(prev_s) <= chunk_overlap:
                            overlap_s.insert(0, prev_s)
                            overlap_len += len(prev_s)
                        else:
                            break
                    curr_sent = overlap_s
                    curr_sent_len = overlap_len
                curr_sent.append(s)
                curr_sent_len += len(s)
            if curr_sent:
                chunks.append(" ".join(curr_sent))
        else:
            if current_len + block_len > chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [block]
                current_len = block_len
            else:
                current_chunk.append(block)
                current_len += block_len + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

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
