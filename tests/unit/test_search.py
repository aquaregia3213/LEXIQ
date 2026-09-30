import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.models import Contract, Document, Chunk
from backend.app.services.embedding import get_embedding_service, DeterministicEmbeddingProvider
from backend.app.services.search import get_search_service, SearchService


@pytest.fixture
def db_session():
    """Isolated in-memory DB session for search tests."""
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
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_contract_dataset(db_session):
    """Populate database with a small realistic contract dataset and vector embeddings."""
    embed_svc = get_embedding_service()

    # Contract A: MSA
    contract_a = Contract(name="Enterprise MSA - Acme Corp", contract_type="Master Services Agreement", status="COMPLETED")
    db_session.add(contract_a)
    db_session.flush()

    doc_a = Document(contract_id=contract_a.id, file_name="acme_msa.pdf", file_type="PDF", page_count=5, processing_status="COMPLETED")
    db_session.add(doc_a)
    db_session.flush()

    text_a1 = "Section 1: Confidentiality. Each party agrees to keep confidential all non-public technical and financial information disclosed under this agreement."
    chunk_a1 = Chunk(
        contract_id=contract_a.id,
        document_id=doc_a.id,
        chunk_index=1,
        text=text_a1,
        page_start=1,
        page_end=1,
        metadata_json={"section": "Confidentiality", "page_start": 1, "page_end": 1},
        embedding=embed_svc.embed_text(text_a1)
    )

    text_a2 = "Section 2: Intellectual Property. Client retains all ownership rights, titles, and interests in and to all work products and custom software deliverables."
    chunk_a2 = Chunk(
        contract_id=contract_a.id,
        document_id=doc_a.id,
        chunk_index=2,
        text=text_a2,
        page_start=2,
        page_end=2,
        metadata_json={"section": "Intellectual Property", "page_start": 2, "page_end": 2},
        embedding=embed_svc.embed_text(text_a2)
    )

    # Contract B: NDA
    contract_b = Contract(name="Mutual NDA - Globex Corp", contract_type="Non-Disclosure Agreement", status="COMPLETED")
    db_session.add(contract_b)
    db_session.flush()

    doc_b = Document(contract_id=contract_b.id, file_name="globex_nda.docx", file_type="DOCX", page_count=2, processing_status="COMPLETED")
    db_session.add(doc_b)
    db_session.flush()

    text_b1 = "Section 1: Definition of Proprietary Data. Confidential information includes proprietary algorithms, customer lists, and financial models."
    chunk_b1 = Chunk(
        contract_id=contract_b.id,
        document_id=doc_b.id,
        chunk_index=1,
        text=text_b1,
        page_start=1,
        page_end=1,
        metadata_json={"section": "Confidentiality", "page_start": 1, "page_end": 1},
        embedding=embed_svc.embed_text(text_b1)
    )

    db_session.add_all([chunk_a1, chunk_a2, chunk_b1])
    db_session.commit()

    return {
        "contract_a": contract_a,
        "contract_b": contract_b,
        "chunks": [chunk_a1, chunk_a2, chunk_b1]
    }


def test_embedding_service_abstraction():
    """Verify embedding service abstraction returns 1536-dimensional normalized vectors."""
    embed_svc = get_embedding_service()
    assert embed_svc.get_dimension() == 1536

    vec = embed_svc.embed_text("Confidentiality and non-disclosure obligations")
    assert isinstance(vec, list)
    assert len(vec) == 1536
    assert all(isinstance(val, float) for val in vec)

    batch_vecs = embed_svc.embed_batch(["Text standard 1", "Text standard 2"])
    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == 1536


def test_semantic_vector_search(db_session, sample_contract_dataset):
    """Verify semantic search retrieves relevant contract chunks based on query intent."""
    search_svc = get_search_service()

    # Query for intellectual property
    results = search_svc.semantic_search(
        db=db_session,
        query="intellectual property deliverables software ownership",
        top_k=5
    )

    assert len(results) >= 1
    top_hit = results[0]
    assert "Intellectual Property" in top_hit["section"] or "ownership" in top_hit["text"]
    assert top_hit["contract_name"] == "Enterprise MSA - Acme Corp"
    assert top_hit["similarity_score"] > 0.0


def test_metadata_filtering(db_session, sample_contract_dataset):
    """Verify semantic search metadata filtering by contract_id and contract_type."""
    search_svc = get_search_service()
    contract_a_id = sample_contract_dataset["contract_a"].id

    # Filter specifically by Contract A
    filtered_results = search_svc.semantic_search(
        db=db_session,
        query="confidential information disclosure",
        contract_id=contract_a_id,
        top_k=5
    )

    assert len(filtered_results) > 0
    for res in filtered_results:
        assert res["contract_id"] == contract_a_id
        assert res["contract_name"] == "Enterprise MSA - Acme Corp"

    # Filter by contract_type NDA
    nda_results = search_svc.semantic_search(
        db=db_session,
        query="proprietary algorithms financial models",
        contract_type="Non-Disclosure",
        top_k=5
    )
    assert len(nda_results) > 0
    assert nda_results[0]["contract_name"] == "Mutual NDA - Globex Corp"


def test_source_reference_validity(db_session, sample_contract_dataset):
    """Verify each retrieved search result contains accurate source references and page bounds."""
    search_svc = get_search_service()
    results = search_svc.semantic_search(
        db=db_session,
        query="confidentiality disclosure agreement",
        top_k=3
    )

    for item in results:
        assert "chunk_id" in item and item["chunk_id"] is not None
        assert "contract_id" in item and item["contract_id"] is not None
        assert "document_id" in item and item["document_id"] is not None
        assert "contract_name" in item
        assert "file_name" in item
        assert item["page_start"] >= 1
        assert item["page_end"] >= item["page_start"]
        assert "section" in item
        assert "similarity_score" in item


def test_search_api_endpoint(client, sample_contract_dataset):
    """Verify POST /api/search REST endpoint execution."""
    payload = {
        "query": "confidential non-public information",
        "top_k": 3,
        "min_score": 0.0
    }

    response = client.post("/api/search", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "confidential non-public information"
    assert data["top_k"] == 3
    assert "results" in data
    assert len(data["results"]) > 0

    first_res = data["results"][0]
    assert "chunk_id" in first_res
    assert "contract_name" in first_res
    assert "page_start" in first_res
    assert "similarity_score" in first_res


def test_empty_query_rejection(client):
    """Verify empty search query is rejected with HTTP 400."""
    response = client.post("/api/search", json={"query": "   "})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]
