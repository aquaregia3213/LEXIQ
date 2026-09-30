import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.models import Contract, Document, Clause, RiskFlag
from backend.app.services.risk_analyzer import (
    RiskAnalyzer, get_risk_analyzer, validate_risk_flag, LEGAL_SAFETY_DISCLAIMER
)


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
def sample_contract_with_risky_clauses(db_session):
    """Populate database with a contract containing risky and non-risky clauses."""
    contract = Contract(name="High Risk Commercial Contract", contract_type="Commercial Agreement", status="COMPLETED")
    db_session.add(contract)
    db_session.flush()

    doc = Document(contract_id=contract.id, file_name="high_risk.pdf", file_type="PDF", page_count=3, processing_status="COMPLETED")
    db_session.add(doc)
    db_session.flush()

    # Risky clauses
    cl1 = Clause(contract_id=contract.id, document_id=doc.id, clause_type="Renewal", text="This contract shall automatically renew for successive 1-year terms unless canceled.", page_number=1, confidence=0.95)
    cl2 = Clause(contract_id=contract.id, document_id=doc.id, clause_type="Liability", text="The parties agree there is no limitation of liability for damages under this agreement.", page_number=2, confidence=0.95)
    cl3 = Clause(contract_id=contract.id, document_id=doc.id, clause_type="Indemnification", text="Contractor agrees to indemnify and hold harmless client against any and all third party claims.", page_number=2, confidence=0.90)
    cl4 = Clause(contract_id=contract.id, document_id=doc.id, clause_type="Termination", text="Licensee has no right to terminate for convenience and must give 120 days written notice.", page_number=3, confidence=0.90)
    cl5 = Clause(contract_id=contract.id, document_id=doc.id, clause_type="Intellectual Property", text="Client retains sole ownership of all inventions and assigns all background intellectual property.", page_number=3, confidence=0.90)

    # Standard non-risky clause
    cl6 = Clause(contract_id=contract.id, document_id=doc.id, clause_type="Confidentiality", text="Each party agrees to maintain non-public information in strict confidence.", page_number=1, confidence=0.95)

    db_session.add_all([cl1, cl2, cl3, cl4, cl5, cl6])
    db_session.commit()

    return contract


def test_risk_detection_categories():
    """Verify evaluation of all 5 target risk categories on risky vs non-risky clause snippets."""
    analyzer = RiskAnalyzer()

    samples = {
        "automatic_renewal": "This agreement shall automatically renew for an additional 12 months.",
        "unlimited_liability": "Neither party shall have a cap on liability for breach of contract.",
        "broad_indemnification": "Contractor shall indemnify and hold harmless Client against any and all liabilities.",
        "restrictive_termination": "Tenant has no right to terminate for convenience prior to expiration.",
        "unusual_ip_provisions": "Vendor transfers all background IP and assigns all pre-existing patents."
    }

    for expected_r_type, text in samples.items():
        risks = analyzer.analyze_clause_text(text)
        assert len(risks) >= 1
        r_types = [r["risk_type"] for r in risks]
        assert expected_r_type in r_types

    # Non-risky clause snippet check
    clean_text = "Either party may terminate upon 30 days notice. Maximum aggregate liability is limited to $10,000."
    clean_risks = analyzer.analyze_clause_text(clean_text)
    assert len(clean_risks) == 0


def test_risk_severity_and_confidence():
    """Verify risk flags assign valid severity levels (LOW, MEDIUM, HIGH) and confidence bounds."""
    analyzer = RiskAnalyzer()
    risks = analyzer.analyze_clause_text("Party agrees there is no cap on liability under any circumstances.")

    assert len(risks) >= 1
    r_item = risks[0]
    assert r_item["severity"] in {"LOW", "MEDIUM", "HIGH"}
    assert 0.0 <= r_item["confidence"] <= 1.0
    assert r_item["evidence"] is not None


def test_risk_legal_disclaimer():
    """Verify explicit legal safety disclaimer labeling on risk analysis results."""
    assert "human review" in LEGAL_SAFETY_DISCLAIMER.lower()
    assert "formal legal advice" in LEGAL_SAFETY_DISCLAIMER.lower()


def test_risk_database_persistence(db_session, sample_contract_with_risky_clauses):
    """Verify risk analysis persistence of RiskFlag ORM models linked to contract_id and clause_id."""
    analyzer = get_risk_analyzer()

    risk_flags = analyzer.analyze_and_store_contract_risks(db=db_session, contract_id=sample_contract_with_risky_clauses.id)
    assert len(risk_flags) >= 5

    saved_flags = db_session.query(RiskFlag).filter(RiskFlag.contract_id == sample_contract_with_risky_clauses.id).all()
    assert len(saved_flags) == len(risk_flags)

    flagged_types = {rf.risk_type for rf in saved_flags}
    assert "automatic_renewal" in flagged_types
    assert "unlimited_liability" in flagged_types
    assert "broad_indemnification" in flagged_types
    assert "restrictive_termination" in flagged_types
    assert "unusual_ip_provisions" in flagged_types

    for rf in saved_flags:
        assert rf.contract_id == sample_contract_with_risky_clauses.id
        assert rf.clause_id is not None
        assert rf.severity in {"LOW", "MEDIUM", "HIGH"}


def test_risk_api_endpoints(client, sample_contract_with_risky_clauses):
    """Verify POST /api/contracts/{id}/analyze-risks and GET /api/contracts/{id}/risks REST routes."""
    contract_id = sample_contract_with_risky_clauses.id

    # 1. POST analyze-risks endpoint
    post_res = client.post(f"/api/contracts/{contract_id}/analyze-risks")
    assert post_res.status_code == 200
    post_data = post_res.json()

    assert post_data["contract_id"] == contract_id
    assert post_data["risk_count"] >= 5
    assert "disclaimer" in post_data
    assert "human review" in post_data["disclaimer"].lower()
    assert len(post_data["risks"]) >= 5

    # 2. GET risks endpoint
    get_res = client.get(f"/api/contracts/{contract_id}/risks")
    assert get_res.status_code == 200
    get_data = get_res.json()

    assert get_data["contract_id"] == contract_id
    assert get_data["risk_count"] == post_data["risk_count"]
    assert len(get_data["risks"]) == len(post_data["risks"])
