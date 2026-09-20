import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_PDF = os.path.join(FIXTURES_DIR, "os_deadlock_sample.pdf")
HINDI_SAMPLE = os.path.join(FIXTURES_DIR, "sample_hindi_doc.docx")

@pytest.fixture
def user_a_headers():
    res = client.post("/api/auth/session", json={"username": "Alice"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def user_b_headers():
    res = client.post("/api/auth/session", json={"username": "Bob"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_unauthenticated_requests_blocked():
    """Unauthenticated requests must be rejected with 401."""
    # List documents
    res = client.get("/api/documents")
    assert res.status_code == 401

    # Chat
    res = client.post("/api/chat", json={"query": "test"})
    assert res.status_code == 401

    # Upload
    with open(SAMPLE_PDF, "rb") as f:
        res = client.post(
            "/api/documents/upload",
            files={"file": ("unauth.pdf", f, "application/pdf")}
        )
    assert res.status_code == 401

    # Download
    res = client.get("/api/documents/fake-id/download")
    assert res.status_code == 401

    # Delete
    res = client.delete("/api/documents/fake-id")
    assert res.status_code == 401

def test_tampered_token_rejected():
    """Tokens with invalid signatures must be rejected with 401."""
    tampered_headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJoYWNrZXIifQ.invalidsig"}
    res = client.get("/api/documents", headers=tampered_headers)
    assert res.status_code == 401

def test_multi_user_upload_and_listing_isolation(user_a_headers, user_b_headers):
    """
    User A and User B upload documents with identical filenames.
    Files and document listings must remain completely isolated.
    """
    # User A uploads os_deadlock_sample.pdf as "common_document.pdf"
    with open(SAMPLE_PDF, "rb") as f:
        res_a = client.post(
            "/api/documents/upload",
            files={"file": ("common_document.pdf", f, "application/pdf")},
            headers=user_a_headers
        )
    assert res_a.status_code == 200
    doc_a_id = res_a.json()["document_id"]

    # User B uploads the same filename "common_document.pdf"
    with open(SAMPLE_PDF, "rb") as f:
        res_b = client.post(
            "/api/documents/upload",
            files={"file": ("common_document.pdf", f, "application/pdf")},
            headers=user_b_headers
        )
    assert res_b.status_code == 200
    doc_b_id = res_b.json()["document_id"]

    # Document IDs must be distinct
    assert doc_a_id != doc_b_id

    # User A listing documents must ONLY contain Document A
    list_a = client.get("/api/documents", headers=user_a_headers)
    assert list_a.status_code == 200
    docs_a = list_a.json()["documents"]
    doc_ids_a = [d["document_id"] for d in docs_a]
    assert doc_a_id in doc_ids_a
    assert doc_b_id not in doc_ids_a

    # User B listing documents must ONLY contain Document B
    list_b = client.get("/api/documents", headers=user_b_headers)
    assert list_b.status_code == 200
    docs_b = list_b.json()["documents"]
    doc_ids_b = [d["document_id"] for d in docs_b]
    assert doc_b_id in doc_ids_b
    assert doc_a_id not in doc_ids_b

    # Cleanup
    client.delete(f"/api/documents/{doc_a_id}", headers=user_a_headers)
    client.delete(f"/api/documents/{doc_b_id}", headers=user_b_headers)

def test_cross_user_access_prevented(user_a_headers, user_b_headers):
    """
    User A cannot get details, download, or delete User B's document.
    """
    # User B uploads a document
    with open(SAMPLE_PDF, "rb") as f:
        res_b = client.post(
            "/api/documents/upload",
            files={"file": ("bob_private.pdf", f, "application/pdf")},
            headers=user_b_headers
        )
    assert res_b.status_code == 200
    doc_b_id = res_b.json()["document_id"]

    # User A tries GET /api/documents/{doc_b_id} -> 404
    res_get = client.get(f"/api/documents/{doc_b_id}", headers=user_a_headers)
    assert res_get.status_code == 404

    # User A tries GET /api/documents/{doc_b_id}/download -> 404
    res_down = client.get(f"/api/documents/{doc_b_id}/download", headers=user_a_headers)
    assert res_down.status_code == 404

    # User A tries DELETE /api/documents/{doc_b_id} -> 404
    res_del = client.delete(f"/api/documents/{doc_b_id}", headers=user_a_headers)
    assert res_del.status_code == 404

    # Verify User B can still access and download the document intact
    res_b_down = client.get(f"/api/documents/{doc_b_id}/download", headers=user_b_headers)
    assert res_b_down.status_code == 200

    # Clean up by User B
    res_b_del = client.delete(f"/api/documents/{doc_b_id}", headers=user_b_headers)
    assert res_b_del.status_code == 200

def test_cross_user_rag_retrieval_isolation(user_a_headers, user_b_headers):
    """
    User A cannot retrieve or cite User B's documents in RAG queries.
    1. Targeted query with User B's document_id returns 404.
    2. Global query by User A for content in User B's document returns not found and zero citations.
    """
    # User B uploads Deadlock document
    with open(SAMPLE_PDF, "rb") as f:
        res_b = client.post(
            "/api/documents/upload",
            files={"file": ("os_deadlock.pdf", f, "application/pdf")},
            headers=user_b_headers
        )
    assert res_b.status_code == 200
    doc_b_id = res_b.json()["document_id"]

    # User A tries targeted query with document_id=doc_b_id -> 404
    chat_a_targeted = client.post(
        "/api/chat",
        json={
            "query": "What is Deadlock?",
            "document_id": doc_b_id
        },
        headers=user_a_headers
    )
    assert chat_a_targeted.status_code == 404

    # User A performs broad query without document_id -> No retrieval from User B's document
    chat_a_broad = client.post(
        "/api/chat",
        json={
            "query": "What are the four necessary conditions for deadlock?"
        },
        headers=user_a_headers
    )
    assert chat_a_broad.status_code == 200
    data_a = chat_a_broad.json()
    assert len(data_a["citations"]) == 0
    # The response must indicate lack of context/information rather than Bob's doc
    ans_lower = data_a["answer"].lower()
    assert any(phrase in ans_lower for phrase in ["not find", "not found", "sufficient information", "not available", "don't know", "no information"])

    # User B queries their own document -> Success with citations
    chat_b = client.post(
        "/api/chat",
        json={
            "query": "What is Deadlock?",
            "document_id": doc_b_id
        },
        headers=user_b_headers
    )
    assert chat_b.status_code == 200
    data_b = chat_b.json()
    assert len(data_b["citations"]) > 0
    assert data_b["citations"][0]["document_id"] == doc_b_id

    # Clean up
    client.delete(f"/api/documents/{doc_b_id}", headers=user_b_headers)

def test_auth_registration_and_login_flow():
    """Test full user registration, login, and profile check flow."""
    import uuid
    username = f"user_{uuid.uuid4().hex[:8]}"
    password = "SuperSecretPassword123!"

    # Register
    reg_res = client.post("/api/auth/register", json={
        "username": username,
        "password": password,
        "email": f"{username}@example.com"
    })
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["user"]["username"] == username
    assert reg_data["user"]["is_guest"] is False
    assert "access_token" in reg_data

    # Duplicate registration blocked
    dup_res = client.post("/api/auth/register", json={
        "username": username,
        "password": password
    })
    assert dup_res.status_code == 400

    # Login
    login_res = client.post("/api/auth/login", json={
        "username": username,
        "password": password
    })
    assert login_res.status_code == 200
    login_token = login_res.json()["access_token"]

    # Check /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == username
