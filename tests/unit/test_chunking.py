import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.models import Contract, Document, Chunk
from ingestion.chunking.chunker import (
    chunk_document_pages, is_section_header, build_chunk_dict
)


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite session fixture using StaticPool."""
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
def sample_parsed_document():
    """Structured sample parsed document containing 2 pages and 3 sections."""
    return {
        "file_type": "PDF",
        "page_count": 2,
        "pages": [
            {
                "page_number": 1,
                "text": (
                    "MASTER SERVICES AGREEMENT\n\n"
                    "Section 1: Confidentiality\n"
                    "Each party agrees to hold all confidential information in strict confidence and shall not disclose it to third parties without prior written consent.\n\n"
                    "Section 2: Intellectual Property\n"
                    "All deliverables created by Contractor under this agreement shall belong exclusively to Client."
                )
            },
            {
                "page_number": 2,
                "text": (
                    "Section 3: Limitation of Liability\n"
                    "In no event shall either party be liable for any special, indirect, or consequential damages arising out of this agreement."
                )
            }
        ]
    }


def test_section_header_detection():
    """Verify section header detection regex rules."""
    assert is_section_header("Section 1: Confidentiality") is True
    assert is_section_header("ARTICLE II - INDEMNIFICATION") is True
    assert is_section_header("1. Governing Law") is True
    assert is_section_header("LIMITATION OF LIABILITY") is True
    assert is_section_header("This is a long paragraph explaining that the party must comply with laws...") is False


def test_semantic_chunk_creation(sample_parsed_document):
    """Verify semantic section-aware chunk creation."""
    chunks = chunk_document_pages(sample_parsed_document)
    assert len(chunks) >= 3

    # Check chunk attributes
    first_chunk = chunks[0]
    assert "chunk_id" in first_chunk
    assert first_chunk["chunk_index"] == 1
    assert first_chunk["page_start"] == 1
    assert "Confidentiality" in first_chunk["text"] or "MASTER SERVICES AGREEMENT" in first_chunk["text"]

    # Verify page 2 chunk page references
    page2_chunks = [c for c in chunks if c["page_start"] == 2]
    assert len(page2_chunks) >= 1
    assert page2_chunks[0]["page_start"] == 2
    assert page2_chunks[0]["page_end"] == 2
    assert "Limitation of Liability" in page2_chunks[0]["text"]


def test_chunk_metadata_preservation(sample_parsed_document):
    """Verify detailed metadata structure is preserved on generated chunks."""
    chunks = chunk_document_pages(sample_parsed_document)
    for chk in chunks:
        meta = chk["metadata"]
        assert "chunk_id" in meta
        assert "chunk_index" in meta
        assert "section" in meta
        assert "page_start" in meta
        assert "page_end" in meta
        assert "char_count" in meta
        assert "word_count" in meta
        assert meta["char_count"] == len(chk["text"])
        assert meta["word_count"] == len(chk["text"].split())


def test_empty_chunk_rejection():
    """Verify empty or whitespace-only document pages generate zero chunks."""
    empty_doc = {
        "file_type": "PDF",
        "page_count": 2,
        "pages": [
            {"page_number": 1, "text": ""},
            {"page_number": 2, "text": "   \n\n  \t  "}
        ]
    }
    chunks = chunk_document_pages(empty_doc)
    assert len(chunks) == 0

    # Build chunk dict empty string rejection test
    with pytest.raises(ValueError, match="Cannot build chunk dictionary for empty text"):
        build_chunk_dict(chunk_index=1, text="   ", page_start=1, page_end=1, section="General")


def test_database_chunk_persistence(db_session, sample_parsed_document):
    """Verify chunks and metadata persist cleanly in database Chunk model."""
    contract = Contract(name="Sample Test Contract", status="PROCESSING")
    db_session.add(contract)
    db_session.flush()

    doc = Document(contract_id=contract.id, file_name="sample.pdf", file_type="PDF")
    db_session.add(doc)
    db_session.flush()

    chunks_data = chunk_document_pages(sample_parsed_document)
    db_chunks = []
    for chk in chunks_data:
        db_chunk = Chunk(
            id=chk["chunk_id"],
            contract_id=contract.id,
            document_id=doc.id,
            chunk_index=chk["chunk_index"],
            text=chk["text"],
            page_start=chk["page_start"],
            page_end=chk["page_end"],
            metadata_json=chk["metadata"]
        )
        db_chunks.append(db_chunk)

    db_session.add_all(db_chunks)
    db_session.commit()

    # Query back chunks
    saved_chunks = db_session.query(Chunk).filter(Chunk.contract_id == contract.id).order_by(Chunk.chunk_index.asc()).all()
    assert len(saved_chunks) == len(chunks_data)
    assert saved_chunks[0].contract_id == contract.id
    assert saved_chunks[0].document_id == doc.id
    assert saved_chunks[0].metadata_json["page_start"] == 1
