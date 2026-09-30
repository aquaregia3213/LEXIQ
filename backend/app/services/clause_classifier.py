import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.models import Contract, Document, Chunk, Clause

ALLOWED_CLAUSE_TYPES = {
    "Termination",
    "Liability",
    "Indemnification",
    "Confidentiality",
    "Payment",
    "Intellectual Property",
    "Data Protection",
    "Non-Compete",
    "Non-Solicitation",
    "Renewal",
    "Governing Law",
    "Dispute Resolution",
    "Other"
}

TAXONOMY_KEYWORDS = {
    "Termination": ["terminate", "termination", "cancel", "cancellation", "expire", "expiration"],
    "Liability": ["limitation of liability", "liable", "liability", "consequential damages", "maximum liability", "punitive damages"],
    "Indemnification": ["indemnify", "indemnification", "hold harmless", "indemnified"],
    "Confidentiality": ["confidential", "confidentiality", "non-disclosure", "proprietary information", "trade secret"],
    "Payment": ["payment", "invoice", "invoices", "compensation", "fee", "fees", "billing", "remit"],
    "Intellectual Property": ["intellectual property", "ip rights", "work product", "deliverables", "copyright", "patent", "trademark", "ownership"],
    "Data Protection": ["data protection", "privacy", "gdpr", "personal data", "data security"],
    "Non-Compete": ["non-compete", "non-competition", "covenant not to compete", "competing business"],
    "Non-Solicitation": ["non-solicitation", "solicit employees", "solicit clients", "no-solicit", "solicitation"],
    "Renewal": ["renewal", "automatic renewal", "extend", "auto-renew", "term extension"],
    "Governing Law": ["governing law", "choice of law", "laws of", "construed in accordance with"],
    "Dispute Resolution": ["dispute resolution", "arbitration", "mediator", "mediation", "court jurisdiction", "litigation"]
}


def classify_clause_text(text: str, section_header: Optional[str] = None) -> Dict[str, Any]:
    """
    Classify clause text snippet into initial clause taxonomy category.
    Evaluates section headers and text content using keyword frequency and pattern matching.
    """
    if not text or not text.strip():
        return {
            "clause_type": "Other",
            "confidence": 0.0,
            "reason": "Text is empty."
        }

    para_lower = text.lower()
    scores: Dict[str, float] = {cat: 0.0 for cat in TAXONOMY_KEYWORDS}

    # 1. Paragraph heading/first line weight
    first_line = para_lower.split("\n")[0]
    for cat, kw_list in TAXONOMY_KEYWORDS.items():
        if any(kw in first_line for kw in kw_list):
            scores[cat] += 4.0

    # 2. Text body weight
    for cat, kw_list in TAXONOMY_KEYWORDS.items():
        for kw in kw_list:
            if kw in para_lower:
                scores[cat] += 2.0

    # 3. Chunk section header weight (secondary context)
    if section_header:
        sec_lower = section_header.lower()
        for cat, kw_list in TAXONOMY_KEYWORDS.items():
            if any(kw in sec_lower for kw in kw_list):
                scores[cat] += 1.0

    best_category = max(scores, key=scores.get)
    max_score = scores[best_category]

    if max_score == 0.0:
        return {
            "clause_type": "Other",
            "confidence": 0.50,
            "reason": "No taxonomy keywords detected."
        }

    confidence = min(0.95, 0.70 + (max_score * 0.08))

    return {
        "clause_type": best_category,
        "confidence": round(confidence, 2),
        "reason": f"Matched taxonomy terms for category '{best_category}' (score: {max_score})."
    }


def validate_clause(clause: Dict[str, Any], contract_text: str) -> bool:
    """
    Validate clause model output before saving.
    Verifies valid taxonomy type, non-empty text, confidence bounds, and source grounding.
    """
    clause_type = clause.get("clause_type")
    text = clause.get("text", "").strip()
    confidence = clause.get("confidence", 1.0)

    if clause_type not in ALLOWED_CLAUSE_TYPES:
        return False

    if not text or len(text) < 10:
        return False

    if not (0.0 <= confidence <= 1.0):
        return False

    # Source grounding check: clause snippet must exist in source document text
    clean_contract = contract_text.lower()
    clean_text = text.lower()

    if clean_text not in clean_contract:
        words = [w for w in re.findall(r"\w+", clean_text) if len(w) > 3]
        if not words or not any(w in clean_contract for w in words):
            return False

    return True


class ClauseClassifier:
    """Service handling clause identification, classification, validation, and storage."""

    def extract_and_store_clauses(
        self,
        db: Session,
        contract_id: str
    ) -> List[Clause]:
        """
        Scan document chunks for contract clauses, classify into taxonomy, and store Clause models.
        """
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError(f"Contract with id '{contract_id}' not found.")

        chunks = db.query(Chunk).filter(Chunk.contract_id == contract_id).order_by(Chunk.chunk_index.asc()).all()
        if not chunks:
            return []

        full_text = "\n\n".join(chunk.text for chunk in chunks)
        db_clauses = []

        for chunk in chunks:
            paragraphs = [p.strip() for p in chunk.text.split("\n\n") if p.strip()]
            section_header = chunk.metadata_json.get("section") if chunk.metadata_json else None

            for para in paragraphs:
                if len(para) < 15:
                    continue

                classification = classify_clause_text(para, section_header=section_header)
                clause_type = classification["clause_type"]

                # We store classified clauses (excluding generic 'Other' when specific clauses exist)
                if clause_type != "Other":
                    item = {
                        "clause_type": clause_type,
                        "text": para,
                        "confidence": classification["confidence"]
                    }

                    if validate_clause(item, full_text):
                        clause_rec = Clause(
                            contract_id=contract_id,
                            document_id=chunk.document_id,
                            clause_type=clause_type,
                            text=para,
                            page_number=chunk.page_start,
                            confidence=classification["confidence"]
                        )
                        db_clauses.append(clause_rec)

        if db_clauses:
            # Idempotent replacement for contract clauses
            db.query(Clause).filter(Clause.contract_id == contract_id).delete()
            db.add_all(db_clauses)
            db.commit()

        return db_clauses


# Default singleton instance
_clause_classifier = ClauseClassifier()


def get_clause_classifier() -> ClauseClassifier:
    """Return default ClauseClassifier instance."""
    return _clause_classifier
