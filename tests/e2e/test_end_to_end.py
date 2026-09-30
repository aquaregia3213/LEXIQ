import io
import fitz  # PyMuPDF
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.services.llm import INSUFFICIENT_EVIDENCE_RESPONSE


@pytest.fixture
def db_session():
    """Isolated in-memory database session fixture."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def contract_pdf_bytes():
    """Create a realistic legal contract in PDF format for end-to-end testing."""
    doc = fitz.open()

    # Page 1: Preamble and Confidentiality
    p1 = doc.new_page()
    p1.insert_text(
        (50, 72),
        "STRATEGIC SOFTWARE LICENSE AGREEMENT\n\n"
        "This Agreement is executed on 2026-06-15 by and between Acme Corp. (Licensor) and Globex Inc. (Licensee).\n"
        "By: Robert Vance\n"
        "Title: Managing Director\n\n"
        "Section 1: Confidential Information\n"
        "Both parties shall maintain strict confidentiality regarding all proprietary source code, algorithms, and business plans."
    )

    # Page 2: Payment Terms and Automatic Renewal
    p2 = doc.new_page()
    p2.insert_text(
        (50, 72),
        "Section 2: Payment Obligations\n"
        "Licensee shall pay $75,000 USD within 30 days of each calendar quarter end.\n\n"
        "Section 3: Term and Renewal\n"
        "This Agreement shall automatically renew for successive 1-year terms unless either party gives 60 days written cancellation notice."
    )

    # Page 3: Liability and Jurisdiction
    p3 = doc.new_page()
    p3.insert_text(
        (50, 72),
        "Section 4: Limitation of Liability\n"
        "The total liability of either party shall not exceed the fees paid in the prior twelve months, subject to a cap on liability.\n\n"
        "Section 5: Governing Law\n"
        "This Agreement shall be governed by the laws of New York."
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_complete_contract_lifecycle_end_to_end(client, contract_pdf_bytes):
    """
    Simulate the complete end-to-end user workflow:
    Upload Contract
          ↓
       Process
          ↓
       Extract (Clauses, Entities, Obligations, Risks)
          ↓
        Index (Vector & Knowledge Graph)
          ↓
     Ask Question
          ↓
       Retrieve
          ↓
    Generate Answer
          ↓
    Display Evidence
    """
    # -------------------------------------------------------------
    # Step 1: Upload Contract
    # -------------------------------------------------------------
    upload_res = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("strategic_agreement.pdf", io.BytesIO(contract_pdf_bytes), "application/pdf")},
        data={"contract_name": "Acme Strategic Software License", "contract_type": "Software License"}
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    contract_id = upload_data["contract_id"]
    assert contract_id is not None
    assert upload_data["processing_status"] == "COMPLETED"
    assert upload_data["page_count"] == 3
    assert upload_data["chunk_count"] >= 3

    # -------------------------------------------------------------
    # Step 2: Check Processing Status & Chunks
    # -------------------------------------------------------------
    status_res = client.get(f"/api/v1/contracts/{contract_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "COMPLETED"

    chunks_res = client.get(f"/api/v1/contracts/{contract_id}/chunks")
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) >= 3
    for chk in chunks:
        assert chk["page_start"] >= 1
        assert "text" in chk and len(chk["text"]) > 0

    # -------------------------------------------------------------
    # Step 3: Extract Clauses
    # -------------------------------------------------------------
    clauses_res = client.post(f"/api/v1/contracts/{contract_id}/extract-clauses")
    assert clauses_res.status_code == 200
    clauses = clauses_res.json()
    assert len(clauses) >= 3
    clause_types = {c["clause_type"] for c in clauses}
    assert "Confidentiality" in clause_types
    assert "Renewal" in clause_types or "Termination" in clause_types

    # -------------------------------------------------------------
    # Step 4: Extract Entities
    # -------------------------------------------------------------
    entities_res = client.post(f"/api/v1/contracts/{contract_id}/extract-entities")
    assert entities_res.status_code == 200
    entities = entities_res.json()
    assert len(entities) >= 3
    entity_types = {e["entity_type"] for e in entities}
    assert "COMPANY" in entity_types
    assert "MONETARY_AMOUNT" in entity_types
    assert "JURISDICTION" in entity_types

    # -------------------------------------------------------------
    # Step 5: Extract Obligations
    # -------------------------------------------------------------
    ob_res = client.post(f"/api/v1/contracts/{contract_id}/extract-obligations")
    assert ob_res.status_code == 200
    obligations = ob_res.json()
    assert len(obligations) >= 1
    assert any("pay" in o["description"].lower() or "confidentiality" in o["description"].lower() for o in obligations)

    # -------------------------------------------------------------
    # Step 6: Risk Analysis
    # -------------------------------------------------------------
    risk_res = client.post(f"/api/v1/contracts/{contract_id}/analyze-risks")
    assert risk_res.status_code == 200
    risk_data = risk_res.json()
    assert "disclaimer" in risk_data
    assert "human review" in risk_data["disclaimer"].lower()
    risks = risk_data["risks"]
    assert len(risks) >= 1
    r_types = {r["risk_type"] for r in risks}
    assert "automatic_renewal" in r_types

    # -------------------------------------------------------------
    # Step 7: Knowledge Graph Synchronization and Query
    # -------------------------------------------------------------
    graph_res = client.post(f"/api/v1/contracts/{contract_id}/sync-graph")
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert graph_data["node_count"] >= 3
    assert graph_data["relationship_count"] >= 2

    # Query contracts involving Acme Corp
    kg_res = client.get("/api/v1/graph/contracts-by-company?company_name=Acme")
    assert kg_res.status_code == 200
    matching_contracts = kg_res.json()
    assert len(matching_contracts) >= 1
    assert matching_contracts[0]["id"] == contract_id

    # -------------------------------------------------------------
    # Step 8: Semantic Search
    # -------------------------------------------------------------
    search_res = client.post(
        "/api/v1/search",
        json={"query": "payment compensation quarterly schedule", "contract_id": contract_id, "top_k": 2}
    )
    assert search_res.status_code == 200
    search_hits = search_res.json()["results"]
    assert len(search_hits) >= 1
    assert "75,000" in search_hits[0]["text"] or "payment" in search_hits[0]["text"].lower()

    # -------------------------------------------------------------
    # Step 9: Grounded RAG Question Answering (Valid Question)
    # -------------------------------------------------------------
    rag_res = client.post(
        "/api/v1/rag/query",
        json={"question": "What are the payment obligations and dollar amount?", "contract_id": contract_id}
    )
    assert rag_res.status_code == 200
    rag_data = rag_res.json()
    assert rag_data["has_sufficient_evidence"] is True
    assert len(rag_data["sources"]) >= 1
    # Check source citation fields
    source = rag_data["sources"][0]
    assert source["page_start"] >= 1
    assert source["contract_id"] == contract_id
    assert source["text"] is not None
    assert "75,000" in rag_data["answer"] or "payment" in rag_data["answer"].lower()

    # -------------------------------------------------------------
    # Step 10: RAG Zero-Hallucination on Unsupported Question
    # -------------------------------------------------------------
    unsupported_res = client.post(
        "/api/v1/rag/query",
        json={"question": "What is the policy for deep sea mining expeditions?", "contract_id": contract_id}
    )
    assert unsupported_res.status_code == 200
    unsupported_data = unsupported_res.json()
    assert unsupported_data["has_sufficient_evidence"] is False
    assert unsupported_data["answer"] == INSUFFICIENT_EVIDENCE_RESPONSE
    assert len(unsupported_data["sources"]) == 0

    # -------------------------------------------------------------
    # Step 11: Contract Deletion & Purge Verification
    # -------------------------------------------------------------
    del_res = client.delete(f"/api/v1/contracts/{contract_id}")
    assert del_res.status_code == 200

    # Verify not found after deletion
    assert client.get(f"/api/v1/contracts/{contract_id}").status_code == 404
