import os
import shutil
import pytest
from backend.app.core.config import settings
from backend.app.services.rag_service import RAGService
from backend.app.schemas.chat import LanguageChoice

@pytest.fixture(scope="module")
def rag_service():
    test_chroma = os.path.join(settings.BASE_DIR, "data", "test_chroma")
    if os.path.exists(test_chroma):
        shutil.rmtree(test_chroma, ignore_errors=True)
        
    rag = RAGService.get_instance()
    
    # Save original state
    orig_vector_store = rag.vector_store
    orig_metadata = dict(rag.documents_metadata)
    orig_registry_file = rag.registry_file

    # Point to test directory and test registry
    from backend.app.services.retrieval.chroma_store import ChromaVectorStore
    rag.vector_store = ChromaVectorStore(persist_dir=test_chroma, collection_name="test_collection")
    rag.registry_file = os.path.join(test_chroma, "test_registry.json")
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

    # Restore original state
    rag.vector_store = orig_vector_store
    rag.documents_metadata = orig_metadata
    rag.registry_file = orig_registry_file

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

@pytest.mark.asyncio
async def test_scenario_7_hindi_doc_hinglish_query(rag_service):
    """Test 7: Hindi document → Hinglish question."""
    answer, citations, det_lang, target_lang = await rag_service.answer_query(
        query="DBMS me primary key ka kya use hota hai?",
        target_language="auto"
    )
    assert len(citations) > 0
    assert "dbms" in citations[0].filename.lower()
    assert det_lang == "hinglish"
    assert target_lang == "hinglish"
    assert len(answer) > 15

@pytest.mark.asyncio
async def test_scenario_8_no_context_multilingual_fallback(rag_service):
    """Test 8: No relevant context → Language-appropriate fallback in Hindi, Hinglish, English."""
    # Hindi query fallback
    ans_hi, cites_hi, _, _ = await rag_service.answer_query(
        query="इस दस्तावेज़ में कंपनी का revenue कितना है?",
        target_language="hi"
    )
    assert "दस्तावेज़" in ans_hi or "पर्याप्त जानकारी नहीं मिली" in ans_hi or len(cites_hi) == 0

    # Hinglish query fallback
    ans_hinglish, cites_hing, _, _ = await rag_service.answer_query(
        query="Is document me company ka revenue kitna hai?",
        target_language="hinglish"
    )
    assert "information nahi mili" in ans_hinglish.lower() or "sufficient" in ans_hinglish.lower() or len(cites_hing) == 0

    # English query fallback
    ans_en, cites_en, _, _ = await rag_service.answer_query(
        query="What is the revenue of the company in this document?",
        target_language="en"
    )
    assert "sufficient information" in ans_en.lower() or "not contain" in ans_en.lower() or len(cites_en) == 0

@pytest.mark.asyncio
async def test_scenario_9_explicit_language_override_hindi_query_english_answer(rag_service):
    """Test 9: Explicit language selection: Query in Hindi, target_language = 'en' → English answer."""
    answer, citations, det_lang, target_lang = await rag_service.answer_query(
        query="डेडलॉक क्या होता है और इसके क्या कारण हैं?",
        target_language="en"
    )
    assert len(citations) > 0
    assert det_lang == "hi"
    assert target_lang == "en"
    assert "according to" in answer.lower() or "deadlock" in answer.lower()

@pytest.mark.asyncio
async def test_scenario_10_explicit_language_override_english_query_hindi_answer(rag_service):
    """Test 10: Explicit language selection: Query in English, target_language = 'hi' → Hindi answer."""
    answer, citations, det_lang, target_lang = await rag_service.answer_query(
        query="What are the conditions for deadlock in operating systems?",
        target_language="hi"
    )
    assert len(citations) > 0
    assert det_lang == "en"
    assert target_lang == "hi"
    assert "दस्तावेज़" in answer or "डेडलॉक" in answer
