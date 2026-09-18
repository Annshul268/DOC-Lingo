import os
import re
from typing import List, Dict, Any
import fitz  # PyMuPDF
import docx

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and remove problematic characters."""
    base = os.path.basename(filename)
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', base)
    return clean

def extract_text_from_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text page-by-page from a PDF using PyMuPDF,
    preserving semantic paragraph and heading boundaries.
    Returns a list of dicts: [{"page_number": 1, "text": "..."}]
    """
    pages_data = []
    doc = fitz.open(file_path)
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            blocks = page.get_text("blocks")
            text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]

            if text_blocks:
                paras = []
                curr_para = []
                prev_y1 = None
                for b in text_blocks:
                    x0, y0, x1, y1, text, bno, btype = b
                    cleaned_line = re.sub(r'[ \t]+', ' ', text).strip()
                    if not cleaned_line:
                        continue
                    # Vertical separation greater than 5 points signifies paragraph/section break
                    if prev_y1 is not None and (y0 - prev_y1 > 5.0):
                        if curr_para:
                            paras.append(" ".join(curr_para))
                            curr_para = []
                    curr_para.append(cleaned_line)
                    prev_y1 = y1
                if curr_para:
                    paras.append(" ".join(curr_para))
                page_text = "\n\n".join(paras).strip()
            else:
                raw_text = page.get_text("text")
                page_text = re.sub(r'[ \t]+', ' ', raw_text).strip()

            if page_text:
                pages_data.append({
                    "page_number": page_idx + 1,
                    "text": page_text
                })
    finally:
        doc.close()
    return pages_data

def extract_text_from_docx(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text from a DOCX document preserving section/paragraph structure.
    Simulates page numbers by batching paragraphs or detecting page breaks.
    """
    doc = docx.Document(file_path)
    pages_data = []
    current_page = 1
    current_text = []
    word_count = 0
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        
        current_text.append(text)
        word_count += len(text.split())
        
        # In docx, standard pages average ~350-400 words
        if word_count >= 350:
            pages_data.append({
                "page_number": current_page,
                "text": "\n".join(current_text)
            })
            current_page += 1
            current_text = []
            word_count = 0
            
    if current_text:
        pages_data.append({
            "page_number": current_page,
            "text": "\n".join(current_text)
        })
        
    return pages_data
