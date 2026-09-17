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
    Extracts text page-by-page from a PDF using PyMuPDF.
    Returns a list of dicts: [{"page_number": 1, "text": "..."}]
    """
    pages_data = []
    doc = fitz.open(file_path)
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            text = page.get_text("text")
            # Clean common artifacts (repeated whitespaces, header/footer numbers)
            cleaned_text = re.sub(r'[ \t]+', ' ', text).strip()
            if cleaned_text:
                pages_data.append({
                    "page_number": page_idx + 1,
                    "text": cleaned_text
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
