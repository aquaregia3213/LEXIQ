import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from backend.app.database import Base


def generate_uuid() -> str:
    """Generate string representation of UUID4 for primary keys."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    """User accounts table."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    # Relationships
    contracts = relationship("Contract", back_populates="user", cascade="all, delete-orphan")


class Contract(Base):
    """Contract metadata and status table."""
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    contract_type = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="PROCESSING", index=True)
    file_path = Column(String(512), nullable=True)
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    # Relationships with cascade deletion
    user = relationship("User", back_populates="contracts")
    documents = relationship("Document", back_populates="contract", cascade="all, delete-orphan")
    clauses = relationship("Clause", back_populates="contract", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="contract", cascade="all, delete-orphan")
    obligations = relationship("Obligation", back_populates="contract", cascade="all, delete-orphan")
    risk_flags = relationship("RiskFlag", back_populates="contract", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="contract", cascade="all, delete-orphan")


class Document(Base):
    """Document files and parsing status associated with contracts."""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    page_count = Column(Integer, default=0)
    processing_status = Column(String(50), nullable=False, default="PENDING", index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    # Relationships
    contract = relationship("Contract", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    clauses = relationship("Clause", back_populates="document", cascade="all, delete-orphan")


class Clause(Base):
    """Extracted and classified contract clauses."""
    __tablename__ = "clauses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    clause_type = Column(String(100), nullable=False, index=True)
    text = Column(Text, nullable=False)
    page_number = Column(Integer, default=1)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    # Relationships
    contract = relationship("Contract", back_populates="clauses")
    document = relationship("Document", back_populates="clauses")
    risk_flags = relationship("RiskFlag", back_populates="clause", cascade="all, delete-orphan")


class Entity(Base):
    """Extracted entities (companies, people, dates, monetary amounts)."""
    __tablename__ = "entities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=True, index=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    # Relationships
    contract = relationship("Contract", back_populates="entities")


class Obligation(Base):
    """Extracted contractual obligations and commitments."""
    __tablename__ = "obligations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    party = Column(String(255), nullable=True)
    deadline = Column(String(255), nullable=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    # Relationships
    contract = relationship("Contract", back_populates="obligations")


class RiskFlag(Base):
    """Identified potential contractual risks and severity assessments."""
    __tablename__ = "risk_flags"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    clause_id = Column(String(36), ForeignKey("clauses.id", ondelete="SET NULL"), nullable=True)
    risk_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, default="MEDIUM", index=True)
    description = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    # Relationships
    contract = relationship("Contract", back_populates="risk_flags")
    clause = relationship("Clause", back_populates="risk_flags")


class Chunk(Base):
    """Document text chunks with metadata and vector embeddings."""
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, index=True)
    text = Column(Text, nullable=False)
    page_start = Column(Integer, default=1)
    page_end = Column(Integer, default=1)
    metadata_json = Column(JSON, nullable=True)
    
    # pgvector embedding (1536 dimensions default for OpenAI text-embedding-3-small)
    # Uses JSON column fallback for SQLite environments
    embedding = Column(
        Vector(1536).with_variant(JSON, "sqlite"),
        nullable=True
    )
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    # Relationships
    contract = relationship("Contract", back_populates="chunks")
    document = relationship("Document", back_populates="chunks")


# Compound and specialized indexes
Index("ix_chunks_contract_chunk", Chunk.contract_id, Chunk.chunk_index)
Index("ix_clauses_contract_type", Clause.contract_id, Clause.clause_type)
Index("ix_entities_contract_norm", Entity.contract_id, Entity.normalized_name)
Index("ix_risk_flags_contract_severity", RiskFlag.contract_id, RiskFlag.severity)
