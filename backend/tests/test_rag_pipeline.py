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
    novatech_pdf = os.path.join(fixtures_dir, "DOC-Lingo_Test_Document_English.pdf")

    # Ingest English PDF
    pdf_meta = rag.process_file(pdf_path, "os_deadlock_sample.pdf")
    assert pdf_meta.page_count == 2
    assert pdf_meta.chunk_count >= 2

    # Ingest Hindi DOCX
    docx_meta = rag.process_file(docx_path, "dbms_hindi_sample.docx")
    assert docx_meta.chunk_count >= 1

    # Ingest Reference English PDF if present
    if os.path.exists(novatech_pdf):
        novatech_meta = rag.process_file(novatech_pdf, "DOC-Lingo_Test_Document_English.pdf")
        assert novatech_meta.page_count >= 3
        assert novatech_meta.chunk_count >= 3

    # Ingest OS Test PDF if present
    os_pdf = os.path.join(fixtures_dir, "DOC-Lingo_OS_Test_Document.pdf")
    if os.path.exists(os_pdf):
        os_meta = rag.process_file(os_pdf, "DOC-Lingo_OS_Test_Document.pdf")
        assert os_meta.page_count == 3
        assert os_meta.chunk_count >= 3

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
    # Cosine similarity for lasagna against documents should not pass threshold or answer indicates not found
    is_not_found = (
        "not contain" in answer.lower() or 
        "sufficient information" in answer.lower() or 
        "no relevant" in answer.lower() or
        "couldn't find" in answer.lower()
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
    # Hindi query fallback (completely absent topic)
    ans_hi, cites_hi, _, _ = await rag_service.answer_query(
        query="इस दस्तावेज़ में मंगल ग्रह (Mars) के मिशन के बारे में क्या लिखा है?",
        target_language="hi"
    )
    assert "दस्तावेज़" in ans_hi or "जानकारी नहीं" in ans_hi or len(cites_hi) == 0

    # Hinglish query fallback (completely absent topic)
    ans_hinglish, cites_hing, _, _ = await rag_service.answer_query(
        query="Is document me Mars mission aur spacecraft ke baare me kya hai?",
        target_language="hinglish"
    )
    assert "information nahi mili" in ans_hinglish.lower() or "sufficient" in ans_hinglish.lower() or "nahi mila" in ans_hinglish.lower() or len(cites_hing) == 0

    # English query fallback (completely absent topic)
    ans_en, cites_en, _, _ = await rag_service.answer_query(
        query="What is the mission launch date of the Mars Rover mentioned in this document?",
        target_language="en"
    )
    assert "sufficient information" in ans_en.lower() or "not contain" in ans_en.lower() or "couldn't find" in ans_en.lower() or len(cites_en) == 0

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

@pytest.mark.asyncio
async def test_scenario_11_revenue_2025_cross_lingual(rag_service):
    """Test 11: 2025 revenue query in English, Hindi, and Hinglish must cite Page 2 and state ₹84 crore."""
    # English
    ans_en, cites_en, det_en, _ = await rag_service.answer_query(
        query="What was NovaTech Solutions' revenue in 2025?",
        target_language="auto"
    )
    assert len(cites_en) > 0
    assert cites_en[0].page_number == 2, f"Expected Page 2 citation, got Page {cites_en[0].page_number}"
    assert "84" in ans_en

    # Hindi
    ans_hi, cites_hi, det_hi, _ = await rag_service.answer_query(
        query="NovaTech Solutions की 2025 में revenue कितनी थी?",
        target_language="auto"
    )
    assert len(cites_hi) > 0
    assert cites_hi[0].page_number == 2
    assert "84" in ans_hi

    # Hinglish
    ans_hing, cites_hing, det_hing, _ = await rag_service.answer_query(
        query="NovaTech Solutions ki 2025 mein revenue kitni thi?",
        target_language="auto"
    )
    assert len(cites_hing) > 0
    assert cites_hing[0].page_number == 2
    assert "84" in ans_hing

@pytest.mark.asyncio
async def test_scenario_12_employees_2025_cross_lingual(rag_service):
    """Test 12: 2025 employees query in English, Hindi, Hinglish must cite Page 2 and return 420 employees."""
    # English
    ans_en, cites_en, _, _ = await rag_service.answer_query(
        query="How many employees did NovaTech Solutions have at the end of 2025?",
        target_language="en"
    )
    assert len(cites_en) > 0
    assert cites_en[0].page_number == 2
    assert "420" in ans_en

    # Hindi
    ans_hi, cites_hi, det_hi, _ = await rag_service.answer_query(
        query="2025 के अंत में NovaTech Solutions में कितने कर्मचारी थे?",
        target_language="auto"
    )
    assert len(cites_hi) > 0
    assert cites_hi[0].page_number == 2
    assert "420" in ans_hi

    # Hinglish
    ans_hing, cites_hing, det_hing, _ = await rag_service.answer_query(
        query="Company me 2025 ke end tak kitne employees the?",
        target_language="auto"
    )
    assert len(cites_hing) > 0
    assert cites_hing[0].page_number == 2
    assert "420" in ans_hing

@pytest.mark.asyncio
async def test_scenario_13_no_context_revenue_2026(rag_service):
    """Test 13: 2026 revenue must NOT hallucinate 2025 revenue (₹84 crore)."""
    ans, cites, _, _ = await rag_service.answer_query(
        query="What was NovaTech's revenue in 2026?",
        target_language="en"
    )
    # Must NOT state 84 or 84 crore as 2026 revenue
    assert "84" not in ans or "couldn't find" in ans.lower() or "not contain" in ans.lower()

@pytest.mark.asyncio
async def test_scenario_14_pilot_start_query(rag_service):
    """Test 14: Pilot start query in Hinglish must retrieve Page 2 and cite October 2025."""
    ans, cites, _, _ = await rag_service.answer_query(
        query="Is document ka DOC-Lingo pilot kab start hua tha?",
        target_language="auto"
    )
    assert len(cites) > 0
    assert cites[0].page_number == 2
    assert "october 2025" in ans.lower() or "october" in ans.lower()

@pytest.mark.asyncio
async def test_scenario_15_os_memory_management_explanation(rag_service):
    """Test 15: Memory management query must return explanatory facts and NOT just a solitary heading."""
    ans, cites, _, _ = await rag_service.answer_query(
        query="What does memory management do in an operating system?",
        target_language="en"
    )
    assert len(cites) > 0
    assert cites[0].page_number in (1, 3)
    # Must NOT be merely the heading
    assert ans.strip().lower() != "memory management"
    # Must contain actual explanatory content
    assert any(term in ans.lower() for term in ["track", "allocat", "virtual memory", "process", "storage"])

@pytest.mark.asyncio
async def test_scenario_16_os_round_robin_hinglish_quality(rag_service):
    """Test 16: Round Robin Hinglish query must return clean Roman-script Hinglish without phonetic mangling."""
    ans, cites, _, _ = await rag_service.answer_query(
        query="Round Robin scheduling kaise kaam karta hai?",
        target_language="hinglish"
    )
    assert len(cites) > 0
    assert cites[0].page_number == 2
    # Must contain technical terms in clean English script
    assert "round robin" in ans.lower()
    assert "quantum" in ans.lower()
    # Must NOT contain phonetically mangled transliterations
    assert "prayoritee" not in ans.lower()
    assert "rॉbin" not in ans

@pytest.mark.asyncio
async def test_scenario_17_os_no_context_market_price(rag_service):
    """Test 17: Out-of-context query about market price in 2026 must return not found and zero citations."""
    ans, cites, _, _ = await rag_service.answer_query(
        query="What is the market price of Linux in 2026?",
        target_language="en"
    )
    assert len(cites) == 0
    assert any(m in ans.lower() for m in ["could not find", "couldn't find", "not find", "no information", "not found", "sufficient information"])

@pytest.mark.asyncio
async def test_scenario_18_os_cross_lingual_linux_type(rag_service):
    """Test 18: Cross-lingual query about Linux type must cite Page 2 and identify open-source."""
    ans, cites, _, _ = await rag_service.answer_query(
        query="Linux kis type ka operating system hai?",
        target_language="hinglish"
    )
    assert len(cites) > 0
    assert cites[0].page_number == 2
    assert "open-source" in ans.lower() or "operating-system" in ans.lower()


