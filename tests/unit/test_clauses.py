import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.models import Contract, Document, Chunk, Clause
from backend.app.services.clause_classifier import (
    ClauseClassifier, get_clause_classifier, classify_clause_text, validate_clause, ALLOWED_CLAUSE_TYPES
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
def sample_contract_with_clauses(db_session):
    """Sample contract containing multi-category clauses across document chunks."""
    contract = Contract(name="Comprehensive Commercial Agreement", contract_type="Commercial Agreement", status="COMPLETED")
    db_session.add(contract)
    db_session.flush()

    doc = Document(contract_id=contract.id, file_name="commercial_agreement.pdf", file_type="PDF", page_count=4, processing_status="COMPLETED")
    db_session.add(doc)
    db_session.flush()

    chunk_1_text = (
        "Section 1: Confidentiality\n"
        "Each party agrees to maintain all non-public technical, financial, and business information in strict confidentiality.\n\n"
        "Section 2: Payment Terms\n"
        "Client shall remit all payments for invoices within 30 days of receipt."
    )

    chunk_2_text = (
        "Section 3: Limitation of Liability\n"
        "In no event shall either party be liable for any consequential or indirect damages. Maximum aggregate liability is limited to total fees paid.\n\n"
        "Section 4: Termination\n"
        "Either party may terminate this agreement upon 30 days written notice for breach."
    )

    c1 = Chunk(
        contract_id=contract.id,
        document_id=doc.id,
        chunk_index=1,
        text=chunk_1_text,
        page_start=1,
        page_end=1,
        metadata_json={"section": "Confidentiality"}
    )
    c2 = Chunk(
        contract_id=contract.id,
        document_id=doc.id,
        chunk_index=2,
        text=chunk_2_text,
        page_start=2,
        page_end=2,
        metadata_json={"section": "Liability"}
    )

    db_session.add_all([c1, c2])
    db_session.commit()

    return contract


def test_clause_taxonomy_classification():
    """Verify classification accuracy across all 12 initial clause taxonomy categories."""
    taxonomy_samples = {
        "Termination": "Either party may terminate this agreement upon 30 days written notice.",
        "Liability": "In no event shall either party be liable for consequential damages or maximum liability.",
        "Indemnification": "Contractor agrees to indemnify and hold harmless Client against third party claims.",
        "Confidentiality": "All proprietary technical information disclosed shall be kept strictly confidential.",
        "Payment": "Client shall pay all invoices and fees within thirty days of billing.",
        "Intellectual Property": "All deliverables, work product, and copyright ownership belong to Client.",
        "Data Protection": "Both parties shall comply with data protection regulations and GDPR privacy rules.",
        "Non-Compete": "Employee agrees not to engage in any competing business during the term.",
        "Non-Solicitation": "Neither party shall solicit employees or clients of the other party.",
        "Renewal": "This agreement shall auto-renew automatically for successive one-year term extensions.",
        "Governing Law": "This contract shall be governed by the choice of law and laws of Delaware.",
        "Dispute Resolution": "Any dispute shall be resolved through binding arbitration and mediation."
    }

    for expected_category, snippet in taxonomy_samples.items():
        res = classify_clause_text(snippet)
        assert res["clause_type"] == expected_category
        assert res["confidence"] >= 0.70
        assert res["clause_type"] in ALLOWED_CLAUSE_TYPES


def test_clause_output_validation():
    """Verify validate_clause rejects invalid taxonomy types, short text, or ungrounded clauses."""
    valid_text = "Either party may terminate this agreement upon 30 days notice."

    # Valid clause
    valid_item = {"clause_type": "Termination", "text": valid_text, "confidence": 0.90}
    assert validate_clause(valid_item, valid_text) is True

    # Invalid category
    invalid_cat = {"clause_type": "INVALID_CATEGORY", "text": valid_text, "confidence": 0.90}
    assert validate_clause(invalid_cat, valid_text) is False

    # Short text
    short_text = {"clause_type": "Termination", "text": "Too short", "confidence": 0.90}
    assert validate_clause(short_text, valid_text) is False

    # Invalid confidence
    bad_conf = {"clause_type": "Termination", "text": valid_text, "confidence": 1.5}
    assert validate_clause(bad_conf, valid_text) is False


def test_clause_database_persistence(db_session, sample_contract_with_clauses):
    """Verify extraction, taxonomy classification, and ORM Clause model storage with page number and confidence."""
    classifier = get_clause_classifier()

    clauses = classifier.extract_and_store_clauses(db=db_session, contract_id=sample_contract_with_clauses.id)
    assert len(clauses) >= 4

    saved_clauses = db_session.query(Clause).filter(Clause.contract_id == sample_contract_with_clauses.id).all()
    assert len(saved_clauses) == len(clauses)

    found_types = {c.clause_type for c in saved_clauses}
    assert "Confidentiality" in found_types
    assert "Payment" in found_types
    assert "Liability" in found_types
    assert "Termination" in found_types

    for c in saved_clauses:
        assert c.contract_id == sample_contract_with_clauses.id
        assert c.document_id is not None
        assert c.page_number >= 1
        assert 0.0 <= c.confidence <= 1.0


def test_clause_api_endpoints(client, sample_contract_with_clauses):
    """Verify POST /api/contracts/{id}/extract-clauses and GET /api/contracts/{id}/clauses."""
    contract_id = sample_contract_with_clauses.id

    # 1. POST extract-clauses
    post_res = client.post(f"/api/contracts/{contract_id}/extract-clauses")
    assert post_res.status_code == 200
    clauses_data = post_res.json()
    assert isinstance(clauses_data, list)
    assert len(clauses_data) >= 4

    # 2. GET clauses
    get_res = client.get(f"/api/contracts/{contract_id}/clauses")
    assert get_res.status_code == 200
    retrieved_data = get_res.json()
    assert len(retrieved_data) == len(clauses_data)
    assert retrieved_data[0]["contract_id"] == contract_id
    assert "clause_type" in retrieved_data[0]
