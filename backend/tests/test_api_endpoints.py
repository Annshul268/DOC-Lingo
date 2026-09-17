import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "DOC-Lingo" in data["app_name"]

def test_upload_and_chat_e2e():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    pdf_path = os.path.join(fixtures_dir, "os_deadlock_sample.pdf")
    
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test_os_deadlock.pdf", f, "application/pdf")}
        )
    assert response.status_code == 200
    doc_data = response.json()
    doc_id = doc_data["document_id"]
    assert doc_id is not None
    assert doc_data["chunk_count"] >= 2

    # Get documents
    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # Chat test - Hinglish question
    chat_res = client.post(
        "/api/chat",
        json={
            "query": "Deadlock kya hota hai?",
            "document_id": doc_id,
            "target_language": "hinglish"
        }
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert len(chat_data["answer"]) > 10
    assert len(chat_data["citations"]) > 0
    assert chat_data["citations"][0]["document_id"] == doc_id
    assert chat_data["target_language"] == "hinglish"

    # Download test
    download_res = client.get(f"/api/documents/{doc_id}/download")
    assert download_res.status_code == 200
    assert len(download_res.content) > 0

    # Clean up document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
