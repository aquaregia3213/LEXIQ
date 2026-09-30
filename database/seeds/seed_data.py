import logging
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.database import engine, init_db, check_db_connection, Base
from backend.app.models.models import (
    Contract, Document, Clause, Entity, Obligation, RiskFlag, Chunk
)

logger = logging.getLogger(__name__)


def create_sample_seed(db: Session) -> Contract:
    """Create sample contract with associated documents, clauses, entities, risks, and chunks."""
    # Sample Contract
    contract = Contract(
        name="Master Services Agreement - Acme Corp & TechProvider Inc",
        contract_type="Master Services Agreement",
        status="COMPLETED",
        file_path="/uploads/contracts/msa_acme_techprovider.pdf"
    )
    db.add(contract)
    db.flush()

    # Sample Document
    doc = Document(
        contract_id=contract.id,
        file_name="msa_acme_techprovider.pdf",
        file_type="PDF",
        page_count=12,
        processing_status="COMPLETED"
    )
    db.add(doc)
    db.flush()

    # Sample Clauses
    termination_clause = Clause(
        contract_id=contract.id,
        document_id=doc.id,
        clause_type="Termination",
        text="Either party may terminate this Agreement upon thirty (30) days written notice to the other party.",
        page_number=8,
        confidence=0.96
    )
    liability_clause = Clause(
        contract_id=contract.id,
        document_id=doc.id,
        clause_type="Liability",
        text="Neither party shall be liable to the other for indirect or consequential damages. Total liability is unlimited.",
        page_number=10,
        confidence=0.92
    )
    renewal_clause = Clause(
        contract_id=contract.id,
        document_id=doc.id,
        clause_type="Renewal",
        text="This Agreement shall automatically renew for successive one-year terms unless cancelled 60 days prior to term end.",
        page_number=12,
        confidence=0.95
    )
    db.add_all([termination_clause, liability_clause, renewal_clause])
    db.flush()

    # Sample Entities
    e1 = Entity(
        contract_id=contract.id,
        entity_type="Company",
        name="Acme Corporation",
        normalized_name="Acme Corp",
        confidence=0.98
    )
    e2 = Entity(
        contract_id=contract.id,
        entity_type="Company",
        name="TechProvider Inc.",
        normalized_name="TechProvider Inc",
        confidence=0.97
    )
    e3 = Entity(
        contract_id=contract.id,
        entity_type="Jurisdiction",
        name="State of California",
        normalized_name="California",
        confidence=0.99
    )
    db.add_all([e1, e2, e3])

    # Sample Obligation
    ob1 = Obligation(
        contract_id=contract.id,
        description="TechProvider Inc. shall deliver quarterly security compliance audits to Acme Corp.",
        party="TechProvider Inc",
        deadline="Quarterly",
        confidence=0.91
    )
    db.add(ob1)

    # Sample Risk Flags
    r1 = RiskFlag(
        contract_id=contract.id,
        clause_id=liability_clause.id,
        risk_type="unlimited_liability",
        severity="HIGH",
        description="Clause specifies unlimited financial liability exposure for Acme Corp.",
        evidence="Total liability is unlimited.",
        confidence=0.89
    )
    r2 = RiskFlag(
        contract_id=contract.id,
        clause_id=renewal_clause.id,
        risk_type="automatic_renewal",
        severity="MEDIUM",
        description="Contract contains an automatic 1-year renewal provision.",
        evidence="This Agreement shall automatically renew for successive one-year terms.",
        confidence=0.94
    )
    db.add_all([r1, r2])

    # Sample Chunk with 1536-dimensional mock embedding vector
    mock_vector = [round(random.uniform(-0.1, 0.1), 6) for _ in range(1536)]
    chunk = Chunk(
        contract_id=contract.id,
        document_id=doc.id,
        chunk_index=1,
        text="Section 10: Limitation of Liability. Neither party shall be liable to the other for indirect or consequential damages. Total liability is unlimited.",
        page_start=10,
        page_end=10,
        metadata_json={"section": "Limitation of Liability", "heading": "Section 10"},
        embedding=mock_vector
    )
    db.add(chunk)
    db.commit()
    db.refresh(contract)
    
    logger.info(f"Successfully seeded contract ID: {contract.id}")
    return contract


def run_seed():
    """Run database initialization and seeding."""
    conn_info = check_db_connection()
    if conn_info.get("status") == "connected":
        db_engine = engine
        logger.info("Seeding connected PostgreSQL database...")
    else:
        logger.info("PostgreSQL unreachable. Running seed using local SQLite database (sqlite:///./legal_ai.db)...")
        db_engine = create_engine("sqlite:///./legal_ai.db", connect_args={"check_same_thread": False})

    init_db(db_engine)
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        contract = create_sample_seed(session)
        print(f"Seed completed successfully! Created Contract ID: {contract.id}")
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_seed()
