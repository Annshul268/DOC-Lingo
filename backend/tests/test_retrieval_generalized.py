import os
import shutil
import pytest
from backend.app.core.config import settings
from backend.app.services.rag_service import RAGService
from backend.app.services.retrieval.chroma_store import ChromaVectorStore

@pytest.fixture(scope="module")
def rag_generalized():
    test_chroma = os.path.join(settings.BASE_DIR, "data", "test_chroma_gen")
    if os.path.exists(test_chroma):
        shutil.rmtree(test_chroma, ignore_errors=True)

    rag = RAGService.get_instance()

    # Save original state
    orig_vector_store = rag.vector_store
    orig_metadata = dict(rag.documents_metadata)
    orig_registry_file = rag.registry_file

    # Use isolated test chroma
    rag.vector_store = ChromaVectorStore(persist_dir=test_chroma, collection_name="test_gen_collection")
    rag.registry_file = os.path.join(test_chroma, "test_gen_registry.json")
    rag.documents_metadata = {}

    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    os_pdf = os.path.join(fixtures_dir, "DOC-Lingo_OS_Test_Document.pdf")
    dbms_pdf = os.path.join(fixtures_dir, "DOC-Lingo_DBMS_Test_Document_v2.pdf")

    # Ingest OS document
    assert os.path.exists(os_pdf), "OS test document must exist"
    os_meta = rag.process_file(os_pdf, "DOC-Lingo_OS_Test_Document.pdf")
    assert os_meta.page_count == 3
    assert os_meta.chunk_count >= 3

    # Ingest DBMS document
    assert os.path.exists(dbms_pdf), "DBMS test document must exist"
    dbms_meta = rag.process_file(dbms_pdf, "DOC-Lingo_DBMS_Test_Document_v2.pdf")
    assert dbms_meta.page_count == 3
    assert dbms_meta.chunk_count >= 3

    yield rag

    # Restore original state
    rag.vector_store = orig_vector_store
    rag.documents_metadata = orig_metadata
    rag.registry_file = orig_registry_file

    if os.path.exists(test_chroma):
        shutil.rmtree(test_chroma, ignore_errors=True)

# -------------------------------------------------------------
# 10 GENERALIZED OS QUESTIONS
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_q1_os_definition(rag_generalized):
    """Q1: Definition intent retrieves Page 1 fundamentals."""
    ans, cites, _, _ = await rag_generalized.answer_query("What is an Operating System?", target_language="en")
    assert len(cites) > 0
    assert cites[0].page_number == 1
    assert any(term in ans.lower() for term in ["interface", "hardware", "software", "resource"])

@pytest.mark.asyncio
async def test_q2_os_types_retrieves_complete_list(rag_generalized):
    """Q2: Types list intent retrieves Page 2 with all operating system types intact."""
    ans, cites, _, _ = await rag_generalized.answer_query("What are the types of Operating Systems?", target_language="en")
    assert len(cites) > 0
    assert cites[0].page_number == 2
    # Verify citations contain all 5 types from Page 2
    full_cites_text = " ".join(c.text_snippet.lower() for c in cites)
    assert "batch" in full_cites_text
    assert "time-sharing" in full_cites_text or "timesharing" in full_cites_text
    assert "real-time" in full_cites_text or "real time" in full_cites_text
    assert "distributed" in full_cites_text
    assert "embedded" in full_cites_text

@pytest.mark.asyncio
async def test_q3_os_functions(rag_generalized):
    """Q3: Function/role intent retrieves Page 1 core responsibilities."""
    ans, cites, _, _ = await rag_generalized.answer_query("What are the key functions of an Operating System?", target_language="en")
    assert len(cites) > 0
    assert cites[0].page_number == 1
    full_cites_text = " ".join(c.text_snippet.lower() for c in cites)
    assert any(f in full_cites_text for f in ["process", "memory", "file", "device", "security"])

@pytest.mark.asyncio
async def test_q4_os_process_mechanism_round_robin(rag_generalized):
    """Q4: Process/mechanism intent retrieves Page 2 CPU scheduling details."""
    ans, cites, _, _ = await rag_generalized.answer_query("How does Round Robin scheduling work?", target_language="en")
    assert len(cites) > 0
    assert cites[0].page_number == 2
    assert any(term in ans.lower() for term in ["time quantum", "slice", "preemptive", "round robin", "cpu"])

@pytest.mark.asyncio
async def test_q5_os_common_operating_systems(rag_generalized):
    """Q5: Common OS examples query retrieves Page 2 Common Operating Systems."""
    ans, cites, _, _ = await rag_generalized.answer_query("What are common operating systems?", target_language="en")
    assert len(cites) > 0
    assert cites[0].page_number == 2
    full_cites_text = " ".join(c.text_snippet.lower() for c in cites)
    assert "linux" in full_cites_text
    assert "windows" in full_cites_text

@pytest.mark.asyncio
async def test_q6_os_file_systems(rag_generalized):
    """Q6: File system query retrieves Page 3 file systems section."""
    ans, cites, _, _ = await rag_generalized.answer_query("What is a file system and what are common examples?", target_language="en")
    assert len(cites) > 0
    assert cites[0].page_number == 3
    full_cites_text = " ".join(c.text_snippet.lower() for c in cites)
    assert any(fs in full_cites_text for fs in ["ext4", "ntfs", "apfs", "fat32"])

@pytest.mark.asyncio
async def test_q7_os_virtual_memory(rag_generalized):
    """Q7: Concept explanation retrieves memory management chunk."""
    ans, cites, _, _ = await rag_generalized.answer_query("What is virtual memory and paging?", target_language="en")
    assert len(cites) > 0
    assert cites[0].page_number in (1, 3)
    full_cites_text = " ".join(c.text_snippet.lower() for c in cites)
    assert "virtual memory" in full_cites_text or "paging" in full_cites_text

@pytest.mark.asyncio
async def test_q8_os_kernel_role(rag_generalized):
    """Q8: Component role intent retrieves Page 1 kernel definition."""
    ans, cites, _, _ = await rag_generalized.answer_query("What is the role of the kernel in an OS?", target_language="en")
    assert len(cites) > 0
    assert cites[0].page_number == 1
    assert "kernel" in ans.lower()

@pytest.mark.asyncio
async def test_q9_os_cross_lingual_types_hinglish(rag_generalized):
    """Q9: Cross-lingual Hinglish query for OS types retrieves Page 2."""
    ans, cites, _, _ = await rag_generalized.answer_query("Operating System ke kaunse types hote hain?", target_language="hinglish")
    assert len(cites) > 0
    assert cites[0].page_number == 2
    full_cites_text = " ".join(c.text_snippet.lower() for c in cites)
    assert "batch" in full_cites_text
    assert "distributed" in full_cites_text

@pytest.mark.asyncio
async def test_q10_os_cross_lingual_functions_hindi(rag_generalized):
    """Q10: Cross-lingual Hindi query for OS functions retrieves Page 1."""
    ans, cites, _, _ = await rag_generalized.answer_query("ऑपरेटिंग सिस्टम के मुख्य कार्य क्या हैं?", target_language="hi")
    assert len(cites) > 0
    assert cites[0].page_number == 1
    assert len(ans) > 10

# -------------------------------------------------------------
# CROSS-DOCUMENT TESTING ON DBMS PDF
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_dbms_q1_definition(rag_generalized):
    """DBMS Q1: Definition intent retrieves Page 1 of DBMS document."""
    ans, cites, _, _ = await rag_generalized.answer_query("What is a Database Management System?", target_language="en")
    assert len(cites) > 0
    assert "dbms" in cites[0].filename.lower()
    assert cites[0].page_number == 1
    assert any(term in ans.lower() for term in ["database", "software", "manage", "store"])

@pytest.mark.asyncio
async def test_dbms_q2_key_difference(rag_generalized):
    """DBMS Q2: Difference query retrieves Primary Key vs Foreign Key from Page 1."""
    ans, cites, _, _ = await rag_generalized.answer_query("What is the difference between a primary key and a foreign key?", target_language="en")
    assert len(cites) > 0
    assert "dbms" in cites[0].filename.lower()
    assert cites[0].page_number == 1
    full_cites_text = " ".join(c.text_snippet.lower() for c in cites)
    assert "primary key" in full_cites_text
    assert "foreign key" in full_cites_text

@pytest.mark.asyncio
async def test_dbms_q3_acid_properties(rag_generalized):
    """DBMS Q3: ACID properties query retrieves Page 2 of DBMS document."""
    ans, cites, _, _ = await rag_generalized.answer_query("What does ACID mean in database transactions?", target_language="en")
    assert len(cites) > 0
    assert "dbms" in cites[0].filename.lower()
    assert cites[0].page_number == 2
    full_cites_text = " ".join(c.text_snippet.lower() for c in cites)
    assert "atomicity" in full_cites_text
    assert "consistency" in full_cites_text
    assert "isolation" in full_cites_text
    assert "durability" in full_cites_text

@pytest.mark.asyncio
async def test_dbms_q4_normalization(rag_generalized):
    """DBMS Q4: Normalization process retrieves Page 2 of DBMS document."""
    ans, cites, _, _ = await rag_generalized.answer_query("How does normalization reduce unnecessary data duplication?", target_language="en")
    assert len(cites) > 0
    assert "dbms" in cites[0].filename.lower()
    assert cites[0].page_number == 2
    full_cites_text = " ".join(c.text_snippet.lower() for c in cites)
    assert "normalization" in full_cites_text

@pytest.mark.asyncio
async def test_dbms_q5_cross_lingual_hindi_keys(rag_generalized):
    """DBMS Q5: Hindi query for Primary vs Foreign Key retrieves Page 1."""
    ans, cites, _, _ = await rag_generalized.answer_query("Primary key aur foreign key mein kya antar hai?", target_language="hi")
    assert len(cites) > 0
    assert "dbms" in cites[0].filename.lower()
    assert cites[0].page_number == 1

@pytest.mark.asyncio
async def test_dbms_q6_no_context_out_of_domain(rag_generalized):
    """DBMS Q6: Out-of-context query about capital of France returns no citations."""
    ans, cites, _, _ = await rag_generalized.answer_query("What is the capital of France?", target_language="en")
    assert len(cites) == 0
    assert any(m in ans.lower() for m in ["could not find", "couldn't find", "not find", "no information", "not found", "sufficient information"])
