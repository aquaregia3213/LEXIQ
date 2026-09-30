import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.services.graph import get_graph_service, GraphService, InMemoryGraphProvider
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.models import Contract, Document, Entity, Clause, Obligation, RiskFlag
@pytest.fixture(autouse=True)
def reset_graph():
    """Reset GraphService in-memory state before each test."""
    svc = get_graph_service()
    svc.provider = InMemoryGraphProvider()
    yield
    svc.provider = InMemoryGraphProvider()


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
    """FastAPI TestClient fixture."""
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
def sample_graph_contract_dataset(db_session):
    """Populate relational database with a contract containing all entity types, clauses, obligations, and risk flags."""
    contract = Contract(name="Global Enterprise Agreement - Acme", contract_type="Enterprise Agreement", status="COMPLETED")
    db_session.add(contract)
    db_session.flush()

    doc = Document(contract_id=contract.id, file_name="global_acme.pdf", file_type="PDF", page_count=5, processing_status="COMPLETED")
    db_session.add(doc)
    db_session.flush()

    # Entities
    e_comp = Entity(contract_id=contract.id, entity_type="COMPANY", name="Acme Inc.", normalized_name="Acme Incorporated", confidence=0.95)
    e_person = Entity(contract_id=contract.id, entity_type="PERSON", name="John Smith", confidence=0.95)
    e_jur = Entity(contract_id=contract.id, entity_type="JURISDICTION", name="State of Delaware", normalized_name="Delaware", confidence=0.95)

    # Clauses
    cl1 = Clause(contract_id=contract.id, document_id=doc.id, clause_type="Termination", text="Either party may terminate upon 30 days notice.", page_number=2, confidence=0.90)
    cl2 = Clause(contract_id=contract.id, document_id=doc.id, clause_type="Confidentiality", text="All trade secrets must remain confidential.", page_number=3, confidence=0.95)

    # Obligations
    ob1 = Obligation(contract_id=contract.id, description="Deliver quarterly compliance reports", party="Acme Inc.", deadline="End of Quarter", confidence=0.90)

    # Risk Flags
    rf1 = RiskFlag(contract_id=contract.id, clause_id=cl1.id, risk_type="UNBALANCED_TERMINATION", severity="HIGH", description="Strict termination clause", confidence=0.85)

    db_session.add_all([e_comp, e_person, e_jur, cl1, cl2, ob1, rf1])
    db_session.commit()

    return contract


def test_graph_node_and_relationship_creation(db_session, sample_graph_contract_dataset):
    """Verify creation of 7 node types and 7 relationship edge types in Knowledge Graph."""
    graph_svc = get_graph_service()

    subgraph = graph_svc.sync_contract_to_graph(db=db_session, contract_id=sample_graph_contract_dataset.id)
    assert subgraph["node_count"] > 0
    assert subgraph["edge_count"] > 0

    node_labels = {n.get("label") for n in subgraph["nodes"]}
    edge_types = {e.get("type") for e in subgraph["edges"]}

    # Verify nodes
    assert "Contract" in node_labels
    assert "Company" in node_labels
    assert "Person" in node_labels
    assert "Clause" in node_labels
    assert "Obligation" in node_labels
    assert "Jurisdiction" in node_labels
    assert "Risk" in node_labels

    # Verify edge types
    assert "PARTY_TO" in edge_types
    assert "SIGNED" in edge_types
    assert "INVOLVES" in edge_types
    assert "CONTAINS" in edge_types
    assert "HAS_OBLIGATION" in edge_types
    assert "GOVERNED_BY" in edge_types
    assert "HAS_RISK" in edge_types


def test_graph_query_contracts_by_company(db_session, sample_graph_contract_dataset):
    """Query 1: Verify finding contracts involving a company."""
    graph_svc = get_graph_service()
    graph_svc.sync_contract_to_graph(db=db_session, contract_id=sample_graph_contract_dataset.id)

    contracts = graph_svc.query_contracts_by_company("Acme Incorporated")
    assert len(contracts) >= 1
    assert contracts[0]["name"] == "Global Enterprise Agreement - Acme"


def test_graph_query_clauses_in_contract(db_session, sample_graph_contract_dataset):
    """Query 2: Verify finding clauses inside a contract."""
    graph_svc = get_graph_service()
    graph_svc.sync_contract_to_graph(db=db_session, contract_id=sample_graph_contract_dataset.id)

    clauses = graph_svc.query_clauses_by_contract(sample_graph_contract_dataset.id)
    assert len(clauses) >= 2
    types = {c["type"] for c in clauses}
    assert "Termination" in types
    assert "Confidentiality" in types


def test_graph_query_obligations_in_contract(db_session, sample_graph_contract_dataset):
    """Query 3: Verify finding obligations belonging to a contract."""
    graph_svc = get_graph_service()
    graph_svc.sync_contract_to_graph(db=db_session, contract_id=sample_graph_contract_dataset.id)

    obligations = graph_svc.query_obligations_by_contract(sample_graph_contract_dataset.id)
    assert len(obligations) >= 1
    assert "quarterly compliance" in obligations[0]["description"]


def test_graph_query_contracts_by_jurisdiction(db_session, sample_graph_contract_dataset):
    """Query 4: Verify finding contracts governed by a jurisdiction."""
    graph_svc = get_graph_service()
    graph_svc.sync_contract_to_graph(db=db_session, contract_id=sample_graph_contract_dataset.id)

    contracts = graph_svc.query_contracts_by_jurisdiction("Delaware")
    assert len(contracts) >= 1
    assert contracts[0]["id"] == sample_graph_contract_dataset.id


def test_graph_entity_normalization(db_session, sample_graph_contract_dataset):
    """Verify company entity resolution maps raw variant (Acme Inc.) to canonical normalized node (Acme Incorporated)."""
    graph_svc = get_graph_service()
    subgraph = graph_svc.sync_contract_to_graph(db=db_session, contract_id=sample_graph_contract_dataset.id)

    comp_nodes = [n for n in subgraph["nodes"] if n.get("label") == "Company"]
    assert len(comp_nodes) >= 1
    assert comp_nodes[0]["normalized_name"] == "Acme Incorporated"


def test_graph_api_endpoints(client, sample_graph_contract_dataset):
    """Verify POST /api/contracts/{id}/sync-graph and GET /api/contracts/{id}/graph REST routes."""
    contract_id = sample_graph_contract_dataset.id

    # 1. Sync POST endpoint
    sync_res = client.post(f"/api/contracts/{contract_id}/sync-graph")
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["contract_id"] == contract_id
    assert sync_data["node_count"] > 0

    # 2. Get Subgraph GET endpoint
    get_res = client.get(f"/api/contracts/{contract_id}/graph")
    assert get_res.status_code == 200
    subgraph_data = get_res.json()
    assert subgraph_data["contract_id"] == contract_id
    assert len(subgraph_data["nodes"]) > 0
    assert len(subgraph_data["edges"]) > 0

    # 3. Query contracts by company GET endpoint
    comp_res = client.get("/api/graph/contracts-by-company?company_name=Acme")
    assert comp_res.status_code == 200
    assert len(comp_res.json()) >= 1

    # 4. Query contracts by jurisdiction GET endpoint
    jur_res = client.get("/api/graph/contracts-by-jurisdiction?jurisdiction_name=Delaware")
    assert jur_res.status_code == 200
    assert len(jur_res.json()) >= 1
