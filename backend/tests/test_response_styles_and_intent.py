import pytest
from backend.app.schemas.chat import ChatRequest, ResponseStyle, LanguageChoice
from backend.app.services.retrieval.query_intent import analyze_query, IntentType
from backend.app.services.generation.prompts import build_user_prompt, STYLE_INSTRUCTIONS
from backend.app.schemas.chat import Citation
from backend.app.services.generation.llm_factory import MockLLMService
from fastapi.testclient import TestClient
from backend.app.main import app

def test_intent_classification_all_types():
    # 1. Definition
    a1 = analyze_query("What is an Operating System?")
    assert a1.intent == IntentType.DEFINITION
    assert "operating" in a1.subject_words or "system" in a1.subject_words or "os" in a1.subject_words

    # 2. Types/List
    a2 = analyze_query("What are the types of Operating Systems?")
    assert a2.intent == IntentType.TYPES_LIST

    # 3. Explanation
    a3 = analyze_query("Explain process management in operating systems")
    assert a3.intent == IntentType.EXPLANATION

    # 4. Reason / Why
    a4 = analyze_query("Why is normalization used in DBMS?")
    assert a4.intent == IntentType.REASON_WHY
    assert "normalization" in a4.subject_words

    # 5. Advantages
    a5 = analyze_query("What are the advantages of Round Robin scheduling?")
    assert a5.intent == IntentType.ADVANTAGES

    # 6. Disadvantages
    a6 = analyze_query("What are the disadvantages or limitations of batch processing?")
    assert a6.intent == IntentType.DISADVANTAGES

    # 7. Comparison
    a7 = analyze_query("Compare paging vs segmentation in memory management")
    assert a7.intent == IntentType.COMPARISON

    # 8. Process / How
    a8 = analyze_query("How does CPU scheduling work?")
    assert a8.intent == IntentType.PROCESS_HOW

    # 9. Summary
    a9 = analyze_query("Summarize the entire document")
    assert a9.intent == IntentType.SUMMARY

    # 10. Factual Lookup
    a10 = analyze_query("How many employees were there in 2025?")
    assert a10.intent == IntentType.FACTUAL_LOOKUP
    assert "2025" in a10.query_years

    # Cross-lingual / Indic intents
    a_hi1 = analyze_query("ऑपरेटिंग सिस्टम के प्रकार क्या हैं?")
    assert a_hi1.intent == IntentType.TYPES_LIST

    a_hi2 = analyze_query("नॉर्मलाइजेशन का क्या कारण है?")
    assert a_hi2.intent == IntentType.REASON_WHY

    a_hing1 = analyze_query("Round Robin kaise kaam karta hai?")
    assert a_hing1.intent == IntentType.PROCESS_HOW

    a_hing2 = analyze_query("Deadlock ke kya fayde aur nuksan hain?")
    assert a_hing2.intent in [IntentType.ADVANTAGES, IntentType.DISADVANTAGES]

def test_chat_request_schema_alias_resolution():
    r1 = ChatRequest(query="test", style="give me points")
    assert r1.response_style == ResponseStyle.POINTS

    r2 = ChatRequest(query="test", response_style="concise")
    assert r2.response_style == ResponseStyle.BRIEFLY

    r3 = ChatRequest(query="test", style="briefly")
    assert r3.response_style == ResponseStyle.BRIEFLY

    r4 = ChatRequest(query="test", style="explain")
    assert r4.response_style == ResponseStyle.EXPLAIN

    r5 = ChatRequest(query="test")
    assert r5.response_style == ResponseStyle.EXPLAIN

def test_build_user_prompt_injects_style_instructions():
    citation = Citation(
        document_id="doc1",
        filename="test.pdf",
        page_number=1,
        chunk_index=0,
        text_snippet="An operating system manages hardware resources.",
        similarity_score=0.9
    )

    prompt_explain = build_user_prompt("What is an OS?", [citation], "en", "explain")
    assert "RESPONSE STYLE: EXPLAIN" in prompt_explain

    prompt_briefly = build_user_prompt("What is an OS?", [citation], "en", "briefly")
    assert "RESPONSE STYLE: BRIEFLY" in prompt_briefly

    prompt_points = build_user_prompt("What is an OS?", [citation], "en", "points")
    assert "RESPONSE STYLE: GIVE ME POINTS" in prompt_points

@pytest.mark.asyncio
async def test_three_response_styles_produce_distinct_grounded_outputs():
    mock_llm = MockLLMService()
    test_citations = [
        Citation(
            document_id="doc_os",
            filename="OS_Guide.pdf",
            page_number=2,
            chunk_index=3,
            text_snippet=(
                "Types of Operating Systems:\n"
                "- Batch Operating System: Groups jobs with similar requirements.\n"
                "- Time-Sharing Operating System: Shares CPU time among active users.\n"
                "- Distributed Operating System: Manages a group of independent computers.\n"
                "- Real-Time Operating System: Provides strict time-critical responses."
            ),
            similarity_score=0.95,
            section_heading="Types of Operating Systems"
        )
    ]
    query = "What are the types of Operating Systems?"

    ans_explain = await mock_llm.generate_response(query, test_citations, "en", response_style="explain")
    ans_briefly = await mock_llm.generate_response(query, test_citations, "en", response_style="briefly")
    ans_points = await mock_llm.generate_response(query, test_citations, "en", response_style="points")

    # 1. Verify grounding (all reference the document)
    assert "OS_Guide.pdf" in ans_explain
    assert "OS_Guide.pdf" in ans_briefly
    assert "OS_Guide.pdf" in ans_points

    # 2. Verify all three outputs are distinctly different
    assert ans_explain != ans_briefly
    assert ans_briefly != ans_points
    assert ans_explain != ans_points

    # 3. Verify Briefly is compact
    assert len(ans_briefly) < len(ans_explain)
    assert "\n" not in ans_briefly.split(": ")[-1]  # Compact single-sentence body

    # 4. Verify Points has genuine bullet formatting
    assert "- Batch Operating System" in ans_points
    assert "- Time-Sharing Operating System" in ans_points
    assert "- Distributed Operating System" in ans_points
    assert ans_points.count("- ") >= 3

@pytest.mark.asyncio
async def test_multilingual_response_styles():
    mock_llm = MockLLMService()
    test_citations = [
        Citation(
            document_id="doc1",
            filename="Company_Report.pdf",
            page_number=2,
            chunk_index=1,
            text_snippet="As of December 2025, the company had 420 full-time employees.",
            similarity_score=0.92
        )
    ]
    query = "Company mein 2025 ke end tak kitne employees the?"

    # Hinglish with Points
    ans_hing_points = await mock_llm.generate_response(query, test_citations, "hinglish", response_style="points")
    assert "420" in ans_hing_points
    assert "- " in ans_hing_points
    assert "Company_Report.pdf" in ans_hing_points

    # Hindi with Briefly
    ans_hi_brief = await mock_llm.generate_response(query, test_citations, "hi", response_style="briefly")
    assert "420" in ans_hi_brief
    assert "Company_Report.pdf" in ans_hi_brief

@pytest.mark.asyncio
async def test_api_chat_and_stream_with_response_style():
    client = TestClient(app)

    # 1. Guest session
    auth_res = client.post("/api/auth/session")
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Chat with response_style="points"
    chat_res = client.post("/api/chat", json={
        "query": "What is an Operating System?",
        "response_style": "points",
        "target_language": "en"
    }, headers=headers)
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "answer" in data
    assert "citations" in data

    # 3. Chat stream with response_style="briefly"
    stream_res = client.post("/api/chat/stream", json={
        "query": "What is an Operating System?",
        "response_style": "briefly",
        "target_language": "en"
    }, headers=headers)
    assert stream_res.status_code == 200
    assert "text/event-stream" in stream_res.headers["content-type"]
