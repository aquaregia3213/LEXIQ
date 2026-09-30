import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.models import Contract, Document, Chunk, Clause, RiskFlag
from backend.app.services.embedding import get_embedding_service
from backend.app.agents.prompts import INSUFFICIENT_EVIDENCE_MESSAGE


@pytest.fixture
def db_session():
    """In-memory database session fixture."""
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
    """FastAPI TestClient fixture with DB override."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def api_test_contract(db_session):
    """Seed test contract data for API integration tests."""
    embed_svc = get_embedding_service()
    contract = Contract(name="SaaS Agreement - CloudInc", contract_type="SaaS Agreement", status="COMPLETED")
    db_session.add(contract)
    db_session.flush()

    doc = Document(contract_id=contract.id, file_name="cloud_saas.pdf", file_type="PDF", page_count=2, processing_status="COMPLETED")
    db_session.add(doc)
    db_session.flush()

    txt_term = "Section 5: Termination. Customer may terminate this subscription upon thirty (30) days written notice."
    chunk_term = Chunk(
        contract_id=contract.id, document_id=doc.id, chunk_index=0,
        text=txt_term, page_start=1, page_end=1,
        metadata_json={"section": "Termination"},
        embedding=embed_svc.embed_text(txt_term)
    )
    clause_term = Clause(
        contract_id=contract.id, document_id=doc.id, clause_type="Termination",
        text=txt_term, page_number=1, confidence=0.94
    )

    txt_risk = "Section 9: Liability. In no event shall provider have any liability cap or limitation of liability."
    chunk_risk = Chunk(
        contract_id=contract.id, document_id=doc.id, chunk_index=1,
        text=txt_risk, page_start=2, page_end=2,
        metadata_json={"section": "Liability"},
        embedding=embed_svc.embed_text(txt_risk)
    )
    clause_risk = Clause(
        contract_id=contract.id, document_id=doc.id, clause_type="Liability",
        text=txt_risk, page_number=2, confidence=0.91
    )
    risk_flag = RiskFlag(
        contract_id=contract.id, clause_id=clause_risk.id, risk_type="unlimited_liability",
        severity="HIGH", description="Potential risk: No liability cap.", evidence="no event shall provider have any liability cap", confidence=0.90
    )

    db_session.add_all([chunk_term, clause_term, chunk_risk, clause_risk, risk_flag])
    db_session.commit()

    return contract


def test_api_list_agent_tools(client):
    """Verify GET /api/v1/agent/tools returns registered tools."""
    response = client.get("/api/v1/agent/tools")
    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    assert len(tools) >= 8

    tool_names = [t["name"] for t in tools]
    assert "search_contract" in tool_names
    assert "get_contract" in tool_names
    assert "get_clauses" in tool_names
    assert "get_risks" in tool_names
    assert "query_knowledge_graph" in tool_names
    assert "retrieve_source" in tool_names
    assert "compare_contracts" in tool_names


def test_api_agent_query_successful(client, api_test_contract):
    """Verify POST /api/v1/agent/query answers legal question with findings and sources."""
    payload = {
        "question": "What is the notice period for terminating the subscription?",
        "contract_id": api_test_contract.id
    }
    response = client.post("/api/v1/agent/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "answer" in data
    assert "summary" in data
    assert "findings" in data
    assert "sources" in data
    assert "tools_used" in data
    assert "confidence" in data
    assert "limitations" in data

    assert len(data["sources"]) > 0
    assert any("30 days" in s["snippet"].lower() or "terminate" in s["snippet"].lower() for s in data["sources"])


def test_api_agent_query_risk(client, api_test_contract):
    """Verify POST /api/v1/agent/query identifies risks."""
    payload = {
        "question": "What are the major liabilities and risks in this agreement?",
        "contract_id": api_test_contract.id
    }
    response = client.post("/api/v1/agent/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "get_risks" in data["tools_used"] or "get_clauses" in data["tools_used"]
    assert any("liability" in f["fact"].lower() for f in data["findings"])


def test_api_agent_query_empty_question(client):
    """Verify POST /api/v1/agent/query validates empty questions."""
    payload = {
        "question": "   ",
        "contract_id": None
    }
    response = client.post("/api/v1/agent/query", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data or "detail" in data


def test_api_agent_query_insufficient_evidence(client, api_test_contract):
    """Verify POST /api/v1/agent/query responds with insufficient evidence without hallucinating."""
    payload = {
        "question": "What is the penalty if source code is transmitted to foreign governments?",
        "contract_id": api_test_contract.id
    }
    response = client.post("/api/v1/agent/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert INSUFFICIENT_EVIDENCE_MESSAGE in data["answer"]
    assert data["confidence"] == "LOW"
