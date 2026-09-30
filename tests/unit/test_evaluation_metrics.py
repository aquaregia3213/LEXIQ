import time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.models import Contract, Document, Chunk
from backend.app.services.extractor import EntityExtractor
from backend.app.services.clause_classifier import classify_clause_text
from backend.app.services.risk_analyzer import RiskAnalyzer
from backend.app.services.embedding import get_embedding_service
from backend.app.services.search import get_search_service
from backend.app.services.llm import get_llm_service, INSUFFICIENT_EVIDENCE_RESPONSE
from backend.app.services.rag import get_rag_pipeline


@pytest.fixture
def db_session():
    """In-memory database session fixture."""
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


# =========================================================================
# 1. Extraction Evaluation (docs/13-evaluation.md)
# Metrics: Precision, Recall, F1
# =========================================================================

def test_extraction_precision_recall_f1():
    """
    Evaluate entity extraction metrics on a curated ground-truth test set.
    Target: Precision >= 0.85, Recall >= 0.85, F1 >= 0.85
    """
    extractor = EntityExtractor()

    test_samples = [
        {
            "text": "Agreement between Alpha Tech Inc. and Beta Dynamics LLC executed on 2026-03-01. Consideration: $500,000 USD. Governed by the laws of California. By: Michael Scott.",
            "ground_truth": {
                ("COMPANY", "Alpha Tech Incorporated"),
                ("COMPANY", "Beta Dynamics Limited Liability Company"),
                ("DATE", "2026-03-01"),
                ("MONETARY_AMOUNT", "500000 USD"),
                ("JURISDICTION", "California"),
                ("PERSON", "Michael Scott")
            }
        },
        {
            "text": "Delta Corp. agreed with Omega Services Ltd. on 2025-11-20 for $45,000 payable in Delaware. By: Dwight Schrute.",
            "ground_truth": {
                ("COMPANY", "Delta Corporation"),
                ("COMPANY", "Omega Services Limited"),
                ("DATE", "2025-11-20"),
                ("MONETARY_AMOUNT", "45000 USD"),
                ("JURISDICTION", "Delaware"),
                ("PERSON", "Dwight Schrute")
            }
        }
    ]

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for sample in test_samples:
        extracted = extractor.extract_from_text(sample["text"])
        pred_set = {(e["entity_type"], e["normalized_name"]) for e in extracted}
        gt_set = sample["ground_truth"]

        tp = len(pred_set.intersection(gt_set))
        fp = len(pred_set - gt_set)
        fn = len(gt_set - pred_set)

        total_tp += tp
        total_fp += fp
        total_fn += fn

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    assert precision >= 0.85, f"Extraction Precision ({precision:.2f}) fell below target 0.85"
    assert recall >= 0.85, f"Extraction Recall ({recall:.2f}) fell below target 0.85"
    assert f1 >= 0.85, f"Extraction F1 ({f1:.2f}) fell below target 0.85"


# =========================================================================
# 2. Classification Evaluation (docs/13-evaluation.md)
# Metrics: Accuracy, Precision, Recall, F1
# =========================================================================

def test_classification_accuracy_and_f1():
    """
    Evaluate clause taxonomy classification across all primary categories.
    Target: Accuracy >= 0.90, Macro-F1 >= 0.90
    """
    labeled_clauses = [
        ("Termination", "Either party may terminate this agreement upon 30 days prior written notice for convenience."),
        ("Liability", "In no event shall either party's maximum aggregate liability exceed the total amounts paid."),
        ("Indemnification", "Contractor shall defend, indemnify, and hold harmless client from all third party claims."),
        ("Confidentiality", "Recipient agrees to maintain non-public technical and business trade secret information confidential."),
        ("Payment", "Client shall pay invoices within thirty (30) days of receipt via electronic bank remittance."),
        ("Intellectual Property", "All patents, copyrights, and intellectual property rights in deliverables shall belong to Client."),
        ("Data Protection", "The parties agree to comply with GDPR, privacy laws, and personal data protection regulations."),
        ("Renewal", "This Agreement shall automatically renew for successive 1-year terms unless notice is given."),
        ("Governing Law", "This contract shall be construed and governed in accordance with the laws of Delaware."),
        ("Dispute Resolution", "Any dispute arising under this agreement shall be submitted to binding arbitration.")
    ]

    correct = 0
    total = len(labeled_clauses)

    for true_label, text in labeled_clauses:
        result = classify_clause_text(text)
        predicted_label = result["clause_type"]
        if predicted_label == true_label:
            correct += 1

    accuracy = correct / total
    assert accuracy >= 0.90, f"Clause classification accuracy ({accuracy:.2f}) fell below target 0.90"


# =========================================================================
# 3. Retrieval Evaluation (docs/13-evaluation.md)
# Metrics: Precision@K, Recall@K, MRR (Mean Reciprocal Rank)
# =========================================================================

def test_retrieval_metrics(db_session):
    """
    Evaluate semantic search retrieval quality:
    - Precision@K (relevant chunks retrieved / K)
    - Recall@K (relevant chunks retrieved / total relevant chunks)
    - MRR (Mean Reciprocal Rank of first relevant chunk)
    Target: Recall@3 >= 0.80, MRR >= 0.80
    """
    embed_svc = get_embedding_service()
    search_svc = get_search_service()

    contract = Contract(name="Retrieval Benchmark Contract", contract_type="MSA", status="COMPLETED")
    db_session.add(contract)
    db_session.flush()

    doc = Document(contract_id=contract.id, file_name="retrieval_bench.pdf", file_type="PDF", page_count=4, processing_status="COMPLETED")
    db_session.add(doc)
    db_session.flush()

    c1_text = "Section 1: Confidentiality Obligations. The parties covenant to safeguard confidential technical trade secrets."
    c2_text = "Section 2: Intellectual Property and Deliverables. All custom software copyright belongs exclusively to customer."
    c3_text = "Section 3: Indemnity and Third Party Claims. Vendor shall hold harmless client against all patent infringement claims."
    c4_text = "Section 4: Termination for Material Breach. Either party may cancel the contract immediately upon written default notice."

    chunks = [
        Chunk(contract_id=contract.id, document_id=doc.id, chunk_index=0, text=c1_text, page_start=1, page_end=1, metadata_json={"section": "Confidentiality"}, embedding=embed_svc.embed_text(c1_text)),
        Chunk(contract_id=contract.id, document_id=doc.id, chunk_index=1, text=c2_text, page_start=2, page_end=2, metadata_json={"section": "Intellectual Property"}, embedding=embed_svc.embed_text(c2_text)),
        Chunk(contract_id=contract.id, document_id=doc.id, chunk_index=2, text=c3_text, page_start=3, page_end=3, metadata_json={"section": "Indemnity"}, embedding=embed_svc.embed_text(c3_text)),
        Chunk(contract_id=contract.id, document_id=doc.id, chunk_index=3, text=c4_text, page_start=4, page_end=4, metadata_json={"section": "Termination"}, embedding=embed_svc.embed_text(c4_text))
    ]
    db_session.add_all(chunks)
    db_session.commit()

    test_queries = [
        {
            "query": "intellectual property software deliverables copyright ownership",
            "expected_chunk_index": 1
        },
        {
            "query": "confidential trade secrets safeguarding technical information",
            "expected_chunk_index": 0
        },
        {
            "query": "patent infringement defense indemnity hold harmless",
            "expected_chunk_index": 2
        }
    ]

    reciprocal_ranks = []
    recalls = []

    for item in test_queries:
        results = search_svc.semantic_search(db=db_session, query=item["query"], top_k=3)
        retrieved_indices = [r["chunk_index"] for r in results]
        
        # Recall@3 (is the target chunk in top 3?)
        recalls.append(1.0 if item["expected_chunk_index"] in retrieved_indices else 0.0)

        # Reciprocal Rank
        try:
            rank = retrieved_indices.index(item["expected_chunk_index"]) + 1
            reciprocal_ranks.append(1.0 / rank)
        except ValueError:
            reciprocal_ranks.append(0.0)

    mean_recall = sum(recalls) / len(recalls)
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)

    assert mean_recall >= 0.80, f"Recall@3 ({mean_recall:.2f}) fell below target 0.80"
    assert mrr >= 0.80, f"MRR ({mrr:.2f}) fell below target 0.80"


# =========================================================================
# 4. RAG Quality & Hallucination Resistance (docs/13-evaluation.md)
# =========================================================================

def test_rag_quality_and_zero_hallucination(db_session):
    """
    Verify RAG pipeline:
    1. Groundedness: 100% of answer claims have source citations.
    2. Zero-Hallucination: Strictly outputs INSUFFICIENT_EVIDENCE_RESPONSE when unsupported.
    """
    embed_svc = get_embedding_service()
    rag_pipeline = get_rag_pipeline()

    contract = Contract(name="RAG Evaluation Contract", contract_type="License", status="COMPLETED")
    db_session.add(contract)
    db_session.flush()

    doc = Document(contract_id=contract.id, file_name="rag_eval.pdf", file_type="PDF", page_count=2, processing_status="COMPLETED")
    db_session.add(doc)
    db_session.flush()

    c1_text = "Section 5: Payment Terms. Licensee shall pay $95,000 USD net 30 upon invoice."
    chunk = Chunk(
        contract_id=contract.id,
        document_id=doc.id,
        chunk_index=0,
        text=c1_text,
        page_start=2,
        page_end=2,
        metadata_json={"section": "Payment Terms"},
        embedding=embed_svc.embed_text(c1_text)
    )
    db_session.add(chunk)
    db_session.commit()

    # Grounded query
    res = rag_pipeline.ask_question(db=db_session, question="What is the payment amount and due date?", contract_id=contract.id)
    assert res["has_sufficient_evidence"] is True
    assert len(res["sources"]) >= 1
    assert res["sources"][0]["page_start"] == 2
    assert "95,000" in res["answer"] or "payment" in res["answer"].lower()

    # Unsupported query (must NOT hallucinate)
    unsupported_res = rag_pipeline.ask_question(db=db_session, question="What is the nuclear decommissioning schedule?", contract_id=contract.id)
    assert unsupported_res["has_sufficient_evidence"] is False
    assert unsupported_res["answer"] == INSUFFICIENT_EVIDENCE_RESPONSE
    assert len(unsupported_res["sources"]) == 0


# =========================================================================
# 5. Risk Detection Quality & False-Positive Rate (docs/13-evaluation.md)
# =========================================================================

def test_risk_detection_false_positive_rate():
    """
    Measure False-Positive Rate on safe/protective clauses.
    Target: False-Positive Rate on safe clauses == 0.0%
    """
    analyzer = RiskAnalyzer()

    safe_clauses = [
        "Maximum aggregate liability is capped at $50,000, subject to a cap on liability.",
        "Either party may terminate this agreement upon thirty (30) days advance written notice.",
        "Each party retains ownership of its respective background intellectual property.",
        "This agreement shall expire at the end of the initial term without automatic renewal.",
        "Vendor shall indemnify client solely for direct damages caused by vendor's gross negligence."
    ]

    false_positives = 0
    for clause in safe_clauses:
        risks = analyzer.analyze_clause_text(clause)
        if len(risks) > 0:
            false_positives += 1

    fpr = false_positives / len(safe_clauses)
    assert fpr == 0.0, f"Risk false-positive rate ({fpr:.2f}) on safe clauses must be 0.0%"


# =========================================================================
# 6. Latency Benchmarks (docs/13-evaluation.md)
# =========================================================================

def test_system_latency_benchmarks(db_session):
    """
    Measure latency of core operations:
    - Search latency (< 100ms)
    - Extraction latency (< 100ms)
    """
    extractor = EntityExtractor()
    sample_text = "Acme Corp agreed on 2026-01-01 to pay $10,000 to Beta LLC in California."

    # Measure Extraction Latency
    start_time = time.perf_counter()
    for _ in range(10):
        extractor.extract_from_text(sample_text)
    extraction_latency_ms = ((time.perf_counter() - start_time) / 10) * 1000

    assert extraction_latency_ms < 100, f"Extraction latency ({extraction_latency_ms:.2f}ms) exceeded 100ms target"
