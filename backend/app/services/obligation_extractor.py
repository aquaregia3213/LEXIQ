import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.models import Contract, Chunk, Clause, Obligation

OBLIGATION_PATTERNS = [
    r"\b([A-Z][A-Za-z0-9\s,]{1,40}?)\s+(shall|must|agrees to|covenants to|undertakes to|is obligated to|is required to)\s+([^.;\n]{10,250})",
    r"\b(Either party|Neither party|Each party|The parties|Both parties)\s+(shall|must|agree to|agree that|agrees to)\s+([^.;\n]{10,250})",
    r"\b([A-Z][A-Za-z0-9\s,]{1,40}?)\s+(will deliver|will provide|will pay|will indemnify)\s+([^.;\n]{10,250})"
]

DEADLINE_PATTERNS = [
    r"\b(within\s+\d+\s+(?:calendar\s+)?(?:days|weeks|months|business\s+days))\b",
    r"\b(prior\s+to\s+[^.,;\n]{3,40})\b",
    r"\b(upon\s+[^.,;\n]{3,40})\b",
    r"\b(by\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\b",
    r"\b(no\s+later\s+than\s+[^.,;\n]{3,40})\b",
    r"\b(at\s+the\s+end\s+of\s+(?:the\s+)?(?:quarter|month|year|term))\b",
    r"\b(quarterly|monthly|annually|bi-annually)\b"
]


def extract_deadline(text: str) -> Optional[str]:
    """Extract temporal deadline constraint from obligation sentence if present."""
    for pattern in DEADLINE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


class ObligationExtractor:
    """Service handling extraction, parsing, and persistence of contractual obligations."""

    def extract_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract obligation items from text snippet using regex pattern detection."""
        if not text or not text.strip():
            return []

        obligations: List[Dict[str, Any]] = []
        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sent in sentences:
            sent_clean = sent.strip()
            if len(sent_clean) < 15:
                continue

            for pat in OBLIGATION_PATTERNS:
                match = re.search(pat, sent_clean, re.IGNORECASE)
                if match:
                    party = match.group(1).strip()
                    action = match.group(2).strip()
                    details = match.group(3).strip()

                    description = f"{party} {action} {details}".strip()
                    # Clean trailing punctuation
                    description = description.rstrip(",; ")
                    deadline = extract_deadline(sent_clean)

                    obligations.append({
                        "description": description,
                        "party": party,
                        "deadline": deadline,
                        "confidence": 0.88
                    })
                    break

        return obligations

    def extract_and_store_obligations(
        self,
        db: Session,
        contract_id: str
    ) -> List[Obligation]:
        """
        Scan document chunks / clauses for a contract, detect obligations, and persist Obligation models.
        """
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError(f"Contract with id '{contract_id}' not found.")

        # Check clauses first, fallback to chunks
        clauses = db.query(Clause).filter(Clause.contract_id == contract_id).all()
        chunks = db.query(Chunk).filter(Chunk.contract_id == contract_id).all()

        text_sources = [c.text for c in clauses] if clauses else [chk.text for chk in chunks]
        if not text_sources:
            return []

        db_obligations: List[Obligation] = []
        seen_descriptions = set()

        for source_text in text_sources:
            extracted = self.extract_from_text(source_text)
            for item in extracted:
                norm_key = item["description"].lower()[:80]
                if norm_key in seen_descriptions:
                    continue
                seen_descriptions.add(norm_key)

                ob_rec = Obligation(
                    contract_id=contract_id,
                    description=item["description"],
                    party=item["party"],
                    deadline=item["deadline"],
                    confidence=item["confidence"]
                )
                db_obligations.append(ob_rec)

        if db_obligations:
            # Delete existing to allow idempotent runs
            db.query(Obligation).filter(Obligation.contract_id == contract_id).delete()
            db.add_all(db_obligations)
            db.commit()

        return db_obligations


_obligation_extractor = ObligationExtractor()


def get_obligation_extractor() -> ObligationExtractor:
    """Return singleton ObligationExtractor instance."""
    return _obligation_extractor
