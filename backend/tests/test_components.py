import os
import pytest
from backend.app.services.language.detector import detect_language
from backend.app.services.ingestion.chunker import split_text_into_chunks, process_and_chunk_document
from backend.app.services.ingestion.extractor import sanitize_filename

def test_language_detection():
    # English test
    assert detect_language("Deadlock occurs when multiple processes wait indefinitely.") == "en"
    assert detect_language("Operating systems manage hardware resources efficiently.") == "en"

    # Hindi test (Devanagari)
    assert detect_language("डेडलॉक एक ऐसी स्थिति है जब कई प्रक्रियाएं एक-दूसरे की प्रतीक्षा करती हैं।") == "hi"
    assert detect_language("कंप्यूटर विज्ञान में यह महत्वपूर्ण है।") == "hi"

    # Hinglish test (Roman script Hindi)
    assert detect_language("Deadlock kya hota hai aur yeh kaise solve hota hai?") == "hinglish"
    assert detect_language("Processes ek doosre ke resources ka wait kyun karte hain?") == "hinglish"
    assert detect_language("Mujhe simple language mein explain karo.") == "hinglish"

def test_sanitize_filename():
    assert sanitize_filename("../../../secret.txt") == "secret.txt"
    assert sanitize_filename("OS Notes (Chapter 1).pdf") == "OS_Notes__Chapter_1_.pdf"

def test_chunker():
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    chunks = split_text_into_chunks(text, chunk_size=30, chunk_overlap=10)
    assert len(chunks) > 1
    assert all(len(c) > 0 for c in chunks)

def test_process_and_chunk_document():
    pages = [
        {"page_number": 1, "text": "Operating system memory management. Virtual memory allows address translation."},
        {"page_number": 2, "text": "Deadlock is a condition where two processes block each other."}
    ]
    chunks = process_and_chunk_document(
        document_id="doc123",
        filename="test.pdf",
        pages_data=pages,
        chunk_size=100,
        chunk_overlap=20
    )
    assert len(chunks) >= 2
    assert chunks[0].page_number == 1
    assert chunks[-1].page_number == 2
    assert chunks[0].document_id == "doc123"
