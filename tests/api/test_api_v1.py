import os
import io
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import fitz

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models.models import Contract, Document, Chunk, Clause, Entity, Obligation, RiskFlag
from backend.app.services.embedding import get_embedding_service
from backend.app.services.graph import get_graph_service, InMemoryGraphProvider


@pytest.fixture(autouse=True)
def reset_graph_state():
    """Reset GraphService in-memory state before and after each test."""
    svc = get_graph_service()
    svc.provider = InMemoryGraphProvider()
    yield
    svc.provider = InMemoryGraphProvider()


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session fixture."""
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
def populated_contract(db_session):
    """Create a fully populated Contract with Chunks, Clauses, Entities, Obligations, and Risks."""
    embed_svc = get_embedding_service()

    contract = Contract(
        name="Apex Enterprise Agreement",
        contract_type="Enterprise Agreement",
        status="COMPLETED"
    )
    db_session.add(contract)
    db_session.flush()

    doc = Document(
        contract_id=contract.id,
        file_name="apex_enterprise.pdf",
        file_type="PDF",
        page_count=3,
        processing_status="COMPLETED"
    )
    db_session.add(doc)
    db_session.flush()

    # Chunks with embeddings
    c1_text = "Section 1: Scope and Confidentiality. Both Apex Corp and Globex Inc agree to maintain strict confidentiality of proprietary data."
    c2_text = "Section 2: Term and Renewal. This Agreement shall automatically renew for additional 1-year terms unless either party gives 60 days notice."
    c3_text = "Section 3: Obligations and Liability. Globex Inc shall deliver quarterly performance reports within 30 days of quarter end. Liability is uncapped."

    vec1 = embed_svc.embed_text(c1_text)
    vec2 = embed_svc.embed_text(c2_text)
    vec3 = embed_svc.embed_text(c3_text)

    chunk1 = Chunk(
        contract_id=contract.id,
        document_id=doc.id,
        chunk_index=0,
        text=c1_text,
        page_start=1,
        page_end=1,
        metadata_json={"section": "Confidentiality"},
        embedding=vec1
    )
    chunk2 = Chunk(
        contract_id=contract.id,
        document_id=doc.id,
        chunk_index=1,
        text=c2_text,
        page_start=2,
        page_end=2,
        metadata_json={"section": "Renewal"},
        embedding=vec2
    )
    chunk3 = Chunk(
        contract_id=contract.id,
        document_id=doc.id,
        chunk_index=2,
        text=c3_text,
        page_start=3,
        page_end=3,
        metadata_json={"section": "Liability"},
        embedding=vec3
    )
    db_session.add_all([chunk1, chunk2, chunk3])
    db_session.flush()

    # Clauses
    cl1 = Clause(
        contract_id=contract.id,
        document_id=doc.id,
        clause_type="Confidentiality",
        text=c1_text,
        page_number=1,
        confidence=0.92
    )
    cl2 = Clause(
        contract_id=contract.id,
        document_id=doc.id,
        clause_type="Renewal",
        text=c2_text,
        page_number=2,
        confidence=0.90
    )
    cl3 = Clause(
        contract_id=contract.id,
        document_id=doc.id,
        clause_type="Liability",
        text=c3_text,
        page_number=3,
        confidence=0.88
    )
    db_session.add_all([cl1, cl2, cl3])
    db_session.flush()

    # Entities
    e1 = Entity(contract_id=contract.id, entity_type="COMPANY", name="Apex Corp", normalized_name="Apex Corporation", confidence=0.95)
    e2 = Entity(contract_id=contract.id, entity_type="COMPANY", name="Globex Inc", normalized_name="Globex Incorporated", confidence=0.95)
    e3 = Entity(contract_id=contract.id, entity_type="JURISDICTION", name="State of New York", normalized_name="New York", confidence=0.90)
    db_session.add_all([e1, e2, e3])

    # Obligations
    ob1 = Obligation(
        contract_id=contract.id,
        description="Globex Inc shall deliver quarterly performance reports within 30 days of quarter end",
        party="Globex Inc",
        deadline="within 30 days of quarter end",
        confidence=0.90
    )
    db_session.add(ob1)

    # Risks
    r1 = RiskFlag(
        contract_id=contract.id,
        clause_id=cl2.id,
        risk_type="automatic_renewal",
        severity="MEDIUM",
        description="Potential risk detected: Clause provides for automatic term renewal.",
        evidence="automatically renew",
        confidence=0.88
    )
    r2 = RiskFlag(
        contract_id=contract.id,
        clause_id=cl3.id,
        risk_type="unlimited_liability",
        severity="HIGH",
        description="Potential risk detected: Clause exposes party to uncapped liability.",
        evidence="uncapped",
        confidence=0.88
    )
    db_session.add_all([r1, r2])

    db_session.commit()
    return contract


@pytest.fixture
def sample_pdf_bytes():
    """Generate in-memory valid PDF bytes for upload tests."""
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 72), "Non-Disclosure Agreement\nSection 1: Confidential Information.\nThe parties agree to maintain secrecy.")
    page2 = doc.new_page()
    page2.insert_text((50, 72), "Section 2: Term and Governing Law.\nThis agreement is governed by the laws of California.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# =========================================================================
# 1. Health Endpoints Tests
# =========================================================================

def test_v1_health(client):
    """Test GET /api/v1/health and root GET /health."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "Legal AI Contract Intelligence API"
    assert "database" in data

    # Root health
    res_root = client.get("/health")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "ok"


# =========================================================================
# 2. Contract Upload Tests
# =========================================================================

def test_v1_contract_upload_success(client, sample_pdf_bytes):
    """Test POST /api/v1/contracts/upload with valid PDF."""
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("nda_agreement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        data={"contract_name": "Mutual NDA", "contract_type": "NDA"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "contract_id" in data
    assert data["filename"] == "nda_agreement.pdf"
    assert data["contract_name"] == "Mutual NDA"
    assert data["processing_status"] == "COMPLETED"
    assert data["page_count"] == 2
    assert data["chunk_count"] >= 1


def test_v1_contract_upload_unsupported_format(client):
    """Test POST /api/v1/contracts/upload with unsupported file extension (.txt)."""
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("contract.txt", io.BytesIO(b"Some plain text"), "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]
    assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_v1_contract_upload_empty_file(client):
    """Test POST /api/v1/contracts/upload with 0-byte file."""
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_v1_contract_upload_corrupted_pdf(client):
    """Test POST /api/v1/contracts/upload with corrupted PDF header."""
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("corrupt.pdf", io.BytesIO(b"INVALID_HEADER_DATA"), "application/pdf")}
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data


# =========================================================================
# 3. Contract Retrieval & Status Tests
# =========================================================================

def test_v1_contract_list(client, populated_contract):
    """Test GET /api/v1/contracts listing."""
    res = client.get("/api/v1/contracts")
    assert res.status_code == 200
    contracts = res.json()
    assert len(contracts) >= 1
    item = contracts[0]
    assert item["id"] == populated_contract.id
    assert item["name"] == "Apex Enterprise Agreement"
    assert item["status"] == "COMPLETED"
    assert item["chunk_count"] == 3


def test_v1_contract_get_details(client, populated_contract):
    """Test GET /api/v1/contracts/{contract_id} metadata and relationships."""
    res = client.get(f"/api/v1/contracts/{populated_contract.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == populated_contract.id
    assert len(data["clauses"]) == 3
    assert len(data["entities"]) == 3
    assert len(data["obligations"]) == 1
    assert len(data["risk_flags"]) == 2


def test_v1_contract_get_not_found(client):
    """Test GET /api/v1/contracts/{contract_id} for non-existent contract."""
    res = client.get("/api/v1/contracts/unknown-contract-id")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_v1_contract_status(client, populated_contract):
    """Test GET /api/v1/contracts/{contract_id}/status."""
    res = client.get(f"/api/v1/contracts/{populated_contract.id}/status")
    assert res.status_code == 200
    data = res.json()
    assert data["contract_id"] == populated_contract.id
    assert data["status"] == "COMPLETED"
    assert data["processing_status"] == "COMPLETED"
    assert data["chunk_count"] == 3


def test_v1_contract_chunks(client, populated_contract):
    """Test GET /api/v1/contracts/{contract_id}/chunks."""
    res = client.get(f"/api/v1/contracts/{populated_contract.id}/chunks")
    assert res.status_code == 200
    chunks = res.json()
    assert len(chunks) == 3
    first = chunks[0]
    assert "chunk_id" in first
    assert "text" in first
    assert "page_start" in first
    assert "source_location" in first
    assert "Page" in first["source_location"]


def test_v1_contract_delete(client, populated_contract):
    """Test DELETE /api/v1/contracts/{contract_id}."""
    res = client.delete(f"/api/v1/contracts/{populated_contract.id}")
    assert res.status_code == 200
    assert "deleted" in res.json()["message"]

    # Verify subsequent GET returns 404
    get_res = client.get(f"/api/v1/contracts/{populated_contract.id}")
    assert get_res.status_code == 404


# =========================================================================
# 4. Semantic Search Tests
# =========================================================================

def test_v1_search_success(client, populated_contract):
    """Test POST /api/v1/search with matching query."""
    res = client.post(
        "/api/v1/search",
        json={"query": "confidentiality and trade secrets", "top_k": 3}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "confidentiality and trade secrets"
    assert data["result_count"] >= 1
    top_result = data["results"][0]
    assert "similarity_score" in top_result
    assert "page_number" in top_result
    assert "source_location" in top_result
    assert top_result["contract_id"] == populated_contract.id


def test_v1_search_with_contract_filter(client, populated_contract):
    """Test POST /api/v1/search scoped to specific contract_id."""
    res = client.post(
        "/api/v1/search",
        json={
            "query": "automatic renewal term",
            "contract_id": populated_contract.id,
            "top_k": 2
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["result_count"] >= 1
    for item in data["results"]:
        assert item["contract_id"] == populated_contract.id


def test_v1_search_empty_query(client):
    """Test POST /api/v1/search with empty query raises 400."""
    res = client.post("/api/v1/search", json={"query": "   "})
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"]


# =========================================================================
# 5. RAG Question-Answering Tests
# =========================================================================

def test_v1_rag_query_success(client, populated_contract):
    """Test POST /api/v1/rag/query grounded question answering with sources."""
    res = client.post(
        "/api/v1/rag/query",
        json={"question": "What are the renewal terms of the contract?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["question"] == "What are the renewal terms of the contract?"
    assert len(data["answer"]) > 0
    assert len(data["sources"]) >= 1
    assert data["has_sufficient_evidence"] is True
    # Verify source citation fields
    src = data["sources"][0]
    assert "contract_name" in src
    assert "page_number" in src
    assert "section" in src


def test_v1_rag_query_insufficient_evidence(client, db_session):
    """Test POST /api/v1/rag/query when no relevant documents exist."""
    empty_contract = Contract(name="Empty Contract", contract_type="General", status="COMPLETED")
    db_session.add(empty_contract)
    db_session.commit()

    res = client.post(
        "/api/v1/rag/query",
        json={"question": "What is the penalty fee?", "contract_id": empty_contract.id}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["has_sufficient_evidence"] is False
    assert "sufficient evidence" in data["answer"].lower()
    assert len(data["sources"]) == 0


def test_v1_rag_query_empty_question(client):
    """Test POST /api/v1/rag/query with empty question raises 400."""
    res = client.post("/api/v1/rag/query", json={"question": ""})
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"]


# =========================================================================
# 6. Clauses Tests
# =========================================================================

def test_v1_clauses_get(client, populated_contract):
    """Test GET /api/v1/contracts/{contract_id}/clauses."""
    res = client.get(f"/api/v1/contracts/{populated_contract.id}/clauses")
    assert res.status_code == 200
    clauses = res.json()
    assert len(clauses) == 3
    c_types = {c["clause_type"] for c in clauses}
    assert "Confidentiality" in c_types
    assert "Renewal" in c_types
    assert "Liability" in c_types
    assert "page_number" in clauses[0]
    assert "source_location" in clauses[0]


def test_v1_clauses_not_found(client):
    """Test GET /api/v1/contracts/{contract_id}/clauses for missing contract."""
    res = client.get("/api/v1/contracts/missing-id/clauses")
    assert res.status_code == 404


def test_v1_clauses_extract_trigger(client, populated_contract):
    """Test POST /api/v1/contracts/{contract_id}/extract-clauses."""
    res = client.post(f"/api/v1/contracts/{populated_contract.id}/extract-clauses")
    assert res.status_code == 200
    assert len(res.json()) >= 1


# =========================================================================
# 7. Entities Tests
# =========================================================================

def test_v1_entities_get(client, populated_contract):
    """Test GET /api/v1/contracts/{contract_id}/entities."""
    res = client.get(f"/api/v1/contracts/{populated_contract.id}/entities")
    assert res.status_code == 200
    entities = res.json()
    assert len(entities) == 3
    names = {e["name"] for e in entities}
    assert "Apex Corp" in names
    assert "Globex Inc" in names
    assert entities[0]["normalized_value"] is not None


def test_v1_entities_not_found(client):
    """Test GET /api/v1/contracts/{contract_id}/entities for missing contract."""
    res = client.get("/api/v1/contracts/missing-id/entities")
    assert res.status_code == 404


def test_v1_entities_extract_trigger(client, populated_contract):
    """Test POST /api/v1/contracts/{contract_id}/extract-entities."""
    res = client.post(f"/api/v1/contracts/{populated_contract.id}/extract-entities")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# =========================================================================
# 8. Obligations Tests
# =========================================================================

def test_v1_obligations_get(client, populated_contract):
    """Test GET /api/v1/contracts/{contract_id}/obligations."""
    res = client.get(f"/api/v1/contracts/{populated_contract.id}/obligations")
    assert res.status_code == 200
    obligations = res.json()
    assert len(obligations) >= 1
    ob = obligations[0]
    assert "quarterly performance" in ob["description"]
    assert ob["responsible_party"] == "Globex Inc"
    assert ob["deadline"] == "within 30 days of quarter end"
    assert ob["confidence"] > 0
    assert "source_location" in ob


def test_v1_obligations_not_found(client):
    """Test GET /api/v1/contracts/{contract_id}/obligations for missing contract."""
    res = client.get("/api/v1/contracts/missing-id/obligations")
    assert res.status_code == 404


def test_v1_obligations_extract_trigger(client, populated_contract):
    """Test POST /api/v1/contracts/{contract_id}/extract-obligations."""
    res = client.post(f"/api/v1/contracts/{populated_contract.id}/extract-obligations")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# =========================================================================
# 9. Risks Tests
# =========================================================================

def test_v1_risks_get(client, populated_contract):
    """Test GET /api/v1/contracts/{contract_id}/risks."""
    res = client.get(f"/api/v1/contracts/{populated_contract.id}/risks")
    assert res.status_code == 200
    data = res.json()
    assert data["contract_id"] == populated_contract.id
    assert data["risk_count"] == 2
    # Verify AI safety disclaimer
    assert "human review only" in data["disclaimer"].lower()
    assert "legal advice" in data["disclaimer"].lower()

    risk_types = {r["risk_type"] for r in data["risks"]}
    assert "automatic_renewal" in risk_types
    assert "unlimited_liability" in risk_types
    assert data["risks"][0]["explanation"] is not None
    assert data["risks"][0]["evidence"] is not None


def test_v1_risks_not_found(client):
    """Test GET /api/v1/contracts/{contract_id}/risks for missing contract."""
    res = client.get("/api/v1/contracts/missing-id/risks")
    assert res.status_code == 404


def test_v1_risks_analyze_trigger(client, populated_contract):
    """Test POST /api/v1/contracts/{contract_id}/analyze-risks."""
    res = client.post(f"/api/v1/contracts/{populated_contract.id}/analyze-risks")
    assert res.status_code == 200
    data = res.json()
    assert data["risk_count"] >= 1
    assert "disclaimer" in data


# =========================================================================
# 10. Knowledge Graph Tests
# =========================================================================

def test_v1_graph_sync_and_get(client, populated_contract):
    """Test POST /api/v1/contracts/{id}/sync-graph and GET /api/v1/contracts/{id}/graph."""
    cid = populated_contract.id

    # 1. Sync
    sync_res = client.post(f"/api/v1/contracts/{cid}/sync-graph")
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["contract_id"] == cid
    assert sync_data["node_count"] > 0
    assert sync_data["relationship_count"] > 0
    assert "nodes" in sync_data
    assert "relationships" in sync_data

    # 2. Get Subgraph
    graph_res = client.get(f"/api/v1/contracts/{cid}/graph")
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert graph_data["contract_id"] == cid
    assert len(graph_data["nodes"]) > 0
    assert len(graph_data["relationships"]) > 0

    # 3. Query contracts by company
    comp_res = client.get("/api/v1/graph/contracts-by-company?company_name=Apex")
    assert comp_res.status_code == 200
    assert len(comp_res.json()) >= 1

    # 4. Query contracts by jurisdiction
    jur_res = client.get("/api/v1/graph/contracts-by-jurisdiction?jurisdiction_name=New York")
    assert jur_res.status_code == 200
    assert len(jur_res.json()) >= 1


def test_v1_graph_not_found(client):
    """Test GET /api/v1/contracts/{id}/graph for non-existent contract."""
    res = client.get("/api/v1/contracts/unknown-contract-id/graph")
    assert res.status_code == 404
