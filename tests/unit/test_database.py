import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, init_db
from backend.app.models.models import (
    User, Contract, Document, Clause, Entity, Obligation, RiskFlag, Chunk
)
from database.seeds.seed_data import create_sample_seed


@pytest.fixture
def in_memory_db():
    """Fixture providing an isolated in-memory SQLite database session for unit tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_models_creation_and_relationships(in_memory_db):
    """Test seeding and querying created models and their relationships."""
    contract = create_sample_seed(in_memory_db)
    assert contract.id is not None
    assert contract.name == "Master Services Agreement - Acme Corp & TechProvider Inc"

    # Query contract with child relationships
    queried = in_memory_db.query(Contract).filter(Contract.id == contract.id).first()
    assert queried is not None
    assert len(queried.documents) == 1
    assert len(queried.clauses) == 3
    assert len(queried.entities) == 3
    assert len(queried.obligations) == 1
    assert len(queried.risk_flags) == 2
    assert len(queried.chunks) == 1

    # Verify chunk embedding vector length
    chunk = queried.chunks[0]
    assert len(chunk.embedding) == 1536
    assert chunk.metadata_json["section"] == "Limitation of Liability"


def test_cascade_deletion(in_memory_db):
    """Test that deleting a contract cascade-deletes all associated child records."""
    contract = create_sample_seed(in_memory_db)
    contract_id = contract.id

    # Verify records exist before deletion
    assert in_memory_db.query(Document).filter(Document.contract_id == contract_id).count() == 1
    assert in_memory_db.query(Clause).filter(Clause.contract_id == contract_id).count() == 3
    assert in_memory_db.query(Entity).filter(Entity.contract_id == contract_id).count() == 3
    assert in_memory_db.query(Obligation).filter(Obligation.contract_id == contract_id).count() == 1
    assert in_memory_db.query(RiskFlag).filter(RiskFlag.contract_id == contract_id).count() == 2
    assert in_memory_db.query(Chunk).filter(Chunk.contract_id == contract_id).count() == 1

    # Delete contract
    in_memory_db.delete(contract)
    in_memory_db.commit()

    # Verify all child records were cascade-deleted
    assert in_memory_db.query(Document).filter(Document.contract_id == contract_id).count() == 0
    assert in_memory_db.query(Clause).filter(Clause.contract_id == contract_id).count() == 0
    assert in_memory_db.query(Entity).filter(Entity.contract_id == contract_id).count() == 0
    assert in_memory_db.query(Obligation).filter(Obligation.contract_id == contract_id).count() == 0
    assert in_memory_db.query(RiskFlag).filter(RiskFlag.contract_id == contract_id).count() == 0
    assert in_memory_db.query(Chunk).filter(Chunk.contract_id == contract_id).count() == 0


def test_metadata_filtering(in_memory_db):
    """Test querying entities and risk flags by metadata attributes."""
    contract = create_sample_seed(in_memory_db)
    
    # Filter entity by normalized name
    company = in_memory_db.query(Entity).filter(
        Entity.contract_id == contract.id,
        Entity.normalized_name == "Acme Corp"
    ).first()
    assert company is not None
    assert company.entity_type == "Company"

    # Filter risk flags by severity
    high_risks = in_memory_db.query(RiskFlag).filter(
        RiskFlag.contract_id == contract.id,
        RiskFlag.severity == "HIGH"
    ).all()
    assert len(high_risks) == 1
    assert high_risks[0].risk_type == "unlimited_liability"
