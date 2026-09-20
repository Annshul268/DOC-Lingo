import re
from typing import List, Dict, Any, Tuple, Optional
from backend.app.core.config import settings
from backend.app.schemas.document import DocumentChunk
from backend.app.services.language.detector import detect_language

def _is_heading_line(line: str) -> bool:
    """Detects if a single line is likely a section heading or title."""
    s = line.strip()
    if not s or len(s) > 80:
        return False
    # If ends in period or semicolon or comma, usually not a section heading
    if s.endswith(('.', '!', '।', ';', ',')):
        return False
    # If starts with bullet or list numbering, it's a list item, not a standalone section heading
    if re.match(r'^(?:\d+[\.\)]|[-*•])\s+', s):
        return False
    # Check for title-like casing or short patterns (allow question headings like "What is an Operating System?")
    words = s.split()
    if 1 <= len(words) <= 10:
        # Avoid common page headers like "Operating Systems ? Test Document" or "Page 1 ? Fundamentals"
        if re.search(r'\bpage\s*\d+\b', s, re.IGNORECASE) or 'test document' in s.lower():
            return False
        return True
    return False

def _extract_section_name(text: str) -> Optional[str]:
    """Extracts the most specific section heading from a block if present."""
    headings = []
    for line in text.split('\n'):
        line = line.strip()
        if _is_heading_line(line):
            clean_h = re.sub(r'^[—–•\-*#\s]+', '', line).strip()
            clean_h = re.sub(r'\s*\?\s*Test Document.*$', '', clean_h, flags=re.IGNORECASE).strip()
            if len(clean_h) > 2 and 'test document' not in clean_h.lower() and not re.search(r'\bpage\s*\d+\b', clean_h, re.IGNORECASE):
                headings.append(clean_h)
    if headings:
        return headings[-1]
    return None

def split_text_into_chunks(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[Tuple[str, Optional[str]]]:
    """
    Split text into coherent semantic chunks preserving headings, lists, and section structure.
    Returns list of tuples: (chunk_text, section_heading).
    """
    if not text or not text.strip():
        return []

    c_size = chunk_size or settings.CHUNK_SIZE
    c_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    # 1. Normalize line breaks
    normalized = re.sub(r'\r\n|\r', '\n', text).strip()
    
    # Clean page header/footer artifacts from the raw text generically
    normalized = re.sub(r'(?m)^[A-Za-z0-9\s—–•?]+\s*[—–•?]\s*Page\s*\d+\s*$', '', normalized)
    normalized = re.sub(r'(?m)^Page\s*\d+\s*[—–•?].*$', '', normalized)
    
    raw_blocks = [b.strip() for b in re.split(r'\n\s*\n', normalized) if b.strip()]
    if not raw_blocks:
        raw_blocks = [normalized]

    # 2. Attach standalone headings to the following content block
    combined_blocks = []
    pending_heading = ""
    for b in raw_blocks:
        lines = [l.strip() for l in b.split('\n') if l.strip()]
        if not lines:
            continue
        if len(lines) == 1 and _is_heading_line(lines[0]):
            if pending_heading:
                pending_heading += "\n" + lines[0]
            else:
                pending_heading = lines[0]
            continue

        if pending_heading:
            combined = f"{pending_heading}\n\n{b}"
            pending_heading = ""
        else:
            combined = b
        combined_blocks.append(combined)

    if pending_heading:
        if combined_blocks:
            combined_blocks[-1] = f"{combined_blocks[-1]}\n\n{pending_heading}"
        else:
            combined_blocks.append(pending_heading)

    # 3. Structure blocks with section names
    structured_units: List[Dict[str, Any]] = []
    active_section = None
    for b in combined_blocks:
        sec = _extract_section_name(b)
        if sec:
            active_section = sec
        structured_units.append({
            "text": b,
            "section": active_section
        })

    # 3. Assemble chunks respecting chunk_size without arbitrarily splitting lists
    chunks_with_sections: List[Tuple[str, Optional[str]]] = []
    current_unit_texts = []
    current_section = None
    current_len = 0

    for unit in structured_units:
        unit_text = unit["text"]
        unit_len = len(unit_text)
        unit_sec = unit["section"]

        # If current chunk plus new unit fits within chunk_size
        if current_len + unit_len + 2 <= c_size:
            current_unit_texts.append(unit_text)
            current_len += unit_len + 2
            if not current_section:
                current_section = unit_sec
        else:
            # Emit current chunk if it has content
            if current_unit_texts:
                full_chunk_text = "\n\n".join(current_unit_texts)
                chunks_with_sections.append((full_chunk_text, current_section))
                current_unit_texts = []
                current_len = 0

            # If the unit by itself is larger than chunk_size, split by sentences
            if unit_len > c_size:
                sentences = re.split(r'(?<=[.?!।])\s+', unit_text)
                curr_sent_list = []
                curr_sent_len = 0
                
                for s in sentences:
                    s = s.strip()
                    if not s:
                        continue
                    if curr_sent_len + len(s) + 1 > c_size and curr_sent_list:
                        chunk_str = " ".join(curr_sent_list)
                        # Prepend section context if continuation
                        if unit_sec and not chunk_str.startswith(unit_sec):
                            chunk_str = f"[{unit_sec}]\n{chunk_str}"
                        chunks_with_sections.append((chunk_str, unit_sec))
                        
                        # Apply overlap
                        overlap_sents = []
                        overlap_l = 0
                        for prev_s in reversed(curr_sent_list):
                            if overlap_l + len(prev_s) <= c_overlap:
                                overlap_sents.insert(0, prev_s)
                                overlap_l += len(prev_s)
                            else:
                                break
                        curr_sent_list = overlap_sents
                        curr_sent_len = overlap_l
                        
                    curr_sent_list.append(s)
                    curr_sent_len += len(s) + 1
                    
                if curr_sent_list:
                    chunk_str = " ".join(curr_sent_list)
                    if unit_sec and not chunk_str.startswith(unit_sec) and len(chunks_with_sections) > 0:
                        chunk_str = f"[{unit_sec}]\n{chunk_str}"
                    chunks_with_sections.append((chunk_str, unit_sec))
                current_section = None
            else:
                current_unit_texts = [unit_text]
                current_len = unit_len
                current_section = unit_sec

    if current_unit_texts:
        full_chunk_text = "\n\n".join(current_unit_texts)
        chunks_with_sections.append((full_chunk_text, current_section))

    return chunks_with_sections

def process_and_chunk_document(
    document_id: str,
    filename: str,
    pages_data: List[Dict[str, Any]],
    chunk_size: int = None,
    chunk_overlap: int = None,
    user_id: str = "default_user"
) -> List[DocumentChunk]:
    """
    Converts page-level extracted data into granular, page-aware, structure-preserving DocumentChunks.
    """
    all_chunks: List[DocumentChunk] = []
    global_chunk_idx = 0
    c_size = chunk_size or settings.CHUNK_SIZE
    c_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    for page_info in pages_data:
        page_num = page_info["page_number"]
        page_text = page_info["text"]
        
        chunks = split_text_into_chunks(page_text, chunk_size=c_size, chunk_overlap=c_overlap)
        for chunk_text, section_heading in chunks:
            lang = detect_language(chunk_text)
            chunk_obj = DocumentChunk(
                chunk_id=f"{document_id}_p{page_num}_c{global_chunk_idx}",
                document_id=document_id,
                user_id=user_id,
                filename=filename,
                page_number=page_num,
                chunk_index=global_chunk_idx,
                text=chunk_text,
                language=lang,
                section_heading=section_heading
            )
            all_chunks.append(chunk_obj)
            global_chunk_idx += 1
            
    return all_chunks
