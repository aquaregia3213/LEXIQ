import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.models import Contract, Document, Chunk, Entity
from backend.app.services.extractor import (
    EntityExtractor, get_entity_extractor, normalize_entity_name, validate_entity
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
def sample_contract_with_chunks(db_session):
    """Sample contract record with chunks containing all target entity types."""
    contract = Contract(name="Master Agreement - Apex Corp", contract_type="Master Agreement", status="COMPLETED")
    db_session.add(contract)
    db_session.flush()

    doc = Document(contract_id=contract.id, file_name="apex_master.pdf", file_type="PDF", page_count=2, processing_status="COMPLETED")
    db_session.add(doc)
    db_session.flush()

    sample_text = (
        "THIS AGREEMENT is entered into on 2026-09-01 by and between Apex Corp. and Globex Inc.\n"
        "By: John Smith\n"
        "Title: Chief Executive Officer\n\n"
        "Section 1: Payment. Client agrees to pay the total sum of $50,000 for consulting services.\n"
        "Payment shall be submitted to the Securities and Exchange Commission oversight body if required.\n\n"
        "Section 12: Governing Law. This contract shall be governed by the laws of New York."
    )

    chunk = Chunk(
        contract_id=contract.id,
        document_id=doc.id,
        chunk_index=1,
        text=sample_text,
        page_start=1,
        page_end=2,
        metadata_json={"section": "Preamble"}
    )

    db_session.add(chunk)
    db_session.commit()

    return contract


def test_entity_type_extraction():
    """Verify extraction of companies, persons, organizations, dates, monetary amounts, and jurisdictions."""
    extractor = EntityExtractor()
    sample_text = (
        "This agreement is made on 2026-01-15 between Acme Inc. and Globex Corp.\n"
        "By: Jane Doe\n"
        "Total consideration: $100,000.\n"
        "Approved by the Securities and Exchange Commission.\n"
        "Governed by the laws of Delaware."
    )

    entities = extractor.extract_from_text(sample_text)
    types_found = {e["entity_type"] for e in entities}

    assert "COMPANY" in types_found
    assert "PERSON" in types_found
    assert "ORGANIZATION" in types_found
    assert "DATE" in types_found
    assert "MONETARY_AMOUNT" in types_found
    assert "JURISDICTION" in types_found


def test_entity_normalization():
    """Verify normalization of corporate forms, currency amounts, and state jurisdictions."""
    assert normalize_entity_name("COMPANY", "Acme Inc.") == "Acme Incorporated"
    assert normalize_entity_name("COMPANY", "Globex Corp.") == "Globex Corporation"
    assert normalize_entity_name("COMPANY", "Apex LLC") == "Apex Limited Liability Company"

    assert normalize_entity_name("MONETARY_AMOUNT", "$50,000") == "50000 USD"
    assert normalize_entity_name("JURISDICTION", "State of New York") == "New York"
    assert normalize_entity_name("PERSON", "By: John Smith") == "John Smith"


def test_entity_output_validation():
    """Verify validate_entity rejects invalid entity types and hallucinated names."""
    valid_text = "Agreement between Apex Corp. and Globex Inc. signed on 2026-05-10."

    # Valid entity
    valid_ent = {"entity_type": "COMPANY", "name": "Apex Corp.", "confidence": 0.95}
    assert validate_entity(valid_ent, valid_text) is True

    # Invalid type
    invalid_type = {"entity_type": "UNSUPPORTED_TYPE", "name": "Apex Corp.", "confidence": 0.95}
    assert validate_entity(invalid_type, valid_text) is False

    # Hallucinated entity not in text
    hallucinated_ent = {"entity_type": "COMPANY", "name": "NonExistent Phantom Corp", "confidence": 0.95}
    assert validate_entity(hallucinated_ent, valid_text) is False


def test_entity_database_persistence(db_session, sample_contract_with_chunks):
    """Verify extraction and persistence of Entity models with valid contract_id references."""
    extractor = get_entity_extractor()

    entities = extractor.extract_and_store_entities(db=db_session, contract_id=sample_contract_with_chunks.id)
    assert len(entities) > 0

    saved_entities = db_session.query(Entity).filter(Entity.contract_id == sample_contract_with_chunks.id).all()
    assert len(saved_entities) == len(entities)

    for ent in saved_entities:
        assert ent.contract_id == sample_contract_with_chunks.id
        assert ent.entity_type in {"COMPANY", "PERSON", "ORGANIZATION", "DATE", "MONETARY_AMOUNT", "JURISDICTION"}
        assert ent.name is not None
        assert ent.normalized_name is not None


def test_entity_api_endpoints(client, sample_contract_with_chunks):
    """Verify POST /api/contracts/{id}/extract-entities and GET /api/contracts/{id}/entities."""
    contract_id = sample_contract_with_chunks.id

    # 1. Trigger extraction POST endpoint
    post_res = client.post(f"/api/contracts/{contract_id}/extract-entities")
    assert post_res.status_code == 200
    extracted_data = post_res.json()
    assert isinstance(extracted_data, list)
    assert len(extracted_data) > 0

    # 2. Retrieve extracted entities GET endpoint
    get_res = client.get(f"/api/contracts/{contract_id}/entities")
    assert get_res.status_code == 200
    retrieved_data = get_res.json()
    assert len(retrieved_data) == len(extracted_data)
    assert retrieved_data[0]["contract_id"] == contract_id
