import os
import shutil
import pytest
from backend.app.core.config import settings
from backend.app.services.rag_service import RAGService
from backend.app.schemas.chat import LanguageChoice

@pytest.fixture(scope="module")
def rag_service():
    # Setup clean test Chroma directory
    test_chroma = os.path.join(settings.BASE_DIR, "data", "test_chroma")
    if os.path.exists(test_chroma):
        shutil.rmtree(test_chroma, ignore_errors=True)
        
    rag = RAGService.get_instance()
    # Use isolated test vector store
    from backend.app.services.retrieval.chroma_store import ChromaVectorStore
    rag.vector_store = ChromaVectorStore(persist_dir=test_chroma, collection_name="test_collection")
    rag.documents_metadata = {}
    
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    pdf_path = os.path.join(fixtures_dir, "os_deadlock_sample.pdf")
    docx_path = os.path.join(fixtures_dir, "dbms_hindi_sample.docx")

    # Ingest English PDF
    pdf_meta = rag.process_file(pdf_path, "os_deadlock_sample.pdf")
    assert pdf_meta.page_count == 2
    assert pdf_meta.chunk_count >= 2

    # Ingest Hindi DOCX
    docx_meta = rag.process_file(docx_path, "dbms_hindi_sample.docx")
    assert docx_meta.chunk_count >= 1

    yield rag

    # Teardown
    if os.path.exists(test_chroma):
        shutil.rmtree(test_chroma, ignore_errors=True)

@pytest.mark.asyncio
async def test_scenario_1_english_doc_english_query(rag_service):
    """Test 1: English document → English question."""
    answer, citations, det_lang, target_lang = await rag_service.answer_query(
        query="What causes deadlock in operating systems?",
        target_language="en"
    )
    assert len(citations) > 0
    top_cite = citations[0]
    assert "deadlock" in top_cite.filename.lower()
    assert top_cite.page_number in [1, 2]
    assert "deadlock" in answer.lower()
    assert len(answer) > 20

@pytest.mark.asyncio
async def test_scenario_2_english_doc_hindi_query(rag_service):
    """Test 2: English document → Hindi question."""
    answer, citations, det_lang, target_lang = await rag_service.answer_query(
        query="डेडलॉक क्या होता है और यह क्यों होता है?",
        target_language="auto"
    )
    assert len(citations) > 0
    # Must retrieve English chunk about deadlock!
    assert "deadlock" in citations[0].text_snippet.lower()
    assert det_lang == "hi"
    assert target_lang == "hi"
    assert len(answer) > 15

@pytest.mark.asyncio
async def test_scenario_3_english_doc_hinglish_query(rag_service):
    """Test 3: English document → Hinglish question."""
    answer, citations, det_lang, target_lang = await rag_service.answer_query(
        query="Deadlock kya hota hai? Simple explain karo.",
        target_language="auto"
    )
    assert len(citations) > 0
    # Must retrieve English chunk about deadlock!
    assert "deadlock" in citations[0].text_snippet.lower()
    assert det_lang == "hinglish"
    assert target_lang == "hinglish"
    assert len(answer) > 15

@pytest.mark.asyncio
async def test_scenario_4_hindi_doc_english_query(rag_service):
    """Test 4: Hindi document → English question."""
    answer, citations, det_lang, target_lang = await rag_service.answer_query(
        query="What is a Primary Key in database management system?",
        target_language="en"
    )
    assert len(citations) > 0
    # Must retrieve Hindi DBMS doc
    assert "dbms" in citations[0].filename.lower()
    assert len(answer) > 15

@pytest.mark.asyncio
async def test_scenario_5_multiple_docs_retrieval(rag_service):
    """Test 5: Multiple documents → relevant document retrieval."""
    docs = rag_service.list_documents()
    assert len(docs) >= 2

    # Query specifically about Banker's Algorithm
    answer, citations, _, _ = await rag_service.answer_query(
        query="Which algorithm is used for deadlock avoidance?",
        target_language="en"
    )
    assert len(citations) > 0
    assert "os_deadlock" in citations[0].filename
    assert "banker" in citations[0].text_snippet.lower()

@pytest.mark.asyncio
async def test_scenario_6_irrelevant_query_not_found(rag_service):
    """Test 6: Question with no relevant information → grounded 'not found' response."""
    answer, citations, _, _ = await rag_service.answer_query(
        query="How to cook Italian lasagna with parmesan cheese and tomato sauce?",
        target_language="en"
    )
    # Cosine similarity for lasagna against OS deadlock / DBMS should not pass threshold or answer indicates not found
    is_not_found = (
        "not contain" in answer.lower() or 
        "sufficient information" in answer.lower() or 
        "no relevant" in answer.lower()
    )
    assert is_not_found or len(citations) == 0 or citations[0].similarity_score < 0.4
