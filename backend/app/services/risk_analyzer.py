import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.models import Contract, Clause, RiskFlag

LEGAL_SAFETY_DISCLAIMER = (
    "This is an AI-generated potential risk flag for human review only. "
    "It does not constitute formal legal advice, legal opinion, or legal certainty."
)

RISK_PATTERNS = {
    "automatic_renewal": {
        "pattern": r"\b(auto(?:matic(?:ally)?)?\s*renew(?:al|s|ed)?|renew\s*automatically)\b",
        "default_severity": "MEDIUM",
        "description": "Potential risk detected: Clause provides for automatic term renewal unless explicit cancellation notice is served. Human review recommended."
    },
    "unlimited_liability": {
        "pattern": r"\b(unlimited\s+liability|no\s+limitation\s+of\s+liability|liability\s+shall\s+not\s+be\s+limited|shall\s+not\s+be\s+limited\s+to|no\s+cap\s+on\s+liability|(?:neither\s+party\s+shall\s+have|without|not?\s+have)\s+(?:a\s+|any\s+)?cap\s+on\s+liability|liability\s+without\s+limitation|uncapped\s+liability|liability\s+is\s+uncapped)\b",
        "default_severity": "HIGH",
        "description": "Potential risk detected: Clause exposes party to uncapped or unlimited monetary liability exposure. Human review recommended."
    },
    "broad_indemnification": {
        "pattern": r"\b(indemnify\b.*\b(any\s+and\s+all|regardless\s+of\s+negligence|solely\s+responsible|all\s+third\s+party\s+claims)|hold\s+harmless\b.*\bany\s+and\s+all)\b",
        "default_severity": "HIGH",
        "description": "Potential risk detected: Clause contains broad or one-sided indemnification requirements. Human review recommended."
    },
    "restrictive_termination": {
        "pattern": r"\b(no\s+right\s+to\s+terminate\s+for\s+convenience|penalty\s+for\s+early\s+termination|(?:90|120|180)\s+days?\s+written\s+notice\s+to\s+terminate|termination\s+fee)\b",
        "default_severity": "MEDIUM",
        "description": "Potential risk detected: Clause imposes restrictive termination conditions, penalties, or long notice periods. Human review recommended."
    },
    "unusual_ip_provisions": {
        "pattern": r"\b(assigns?\s+all\s+(?:background\s+)?intellectual\s+property|transfers?\s+all\s+background\s+ip|sole\s+ownership\s+of\s+all\s+inventions|irrevocable\s+assignment)\b",
        "default_severity": "HIGH",
        "description": "Potential risk detected: Clause requires broad assignment of intellectual property or background assets. Human review recommended."
    }
}


def validate_risk_flag(risk: Dict[str, Any], clause_text: str) -> bool:
    """
    Validate risk flag dictionary before saving.
    Verifies valid risk category, severity level, confidence bounds, and evidence text grounding.
    """
    risk_type = risk.get("risk_type")
    severity = risk.get("severity")
    confidence = risk.get("confidence", 1.0)
    evidence = risk.get("evidence", "").strip()

    if risk_type not in RISK_PATTERNS:
        return False

    if severity not in {"LOW", "MEDIUM", "HIGH"}:
        return False

    if not (0.0 <= confidence <= 1.0):
        return False

    if not evidence or len(evidence) < 5:
        return False

    # Evidence grounding verification
    if evidence.lower() not in clause_text.lower():
        words = [w for w in re.findall(r"\w+", evidence.lower()) if len(w) > 3]
        if not words or not any(w in clause_text.lower() for w in words):
            return False

    return True


class RiskAnalyzer:
    """Service executing hybrid risk analysis across contract clauses."""

    def analyze_clause_text(
        self,
        clause_text: str,
        clause_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze a single clause snippet for potential risks across the 5 target categories.
        """
        if not clause_text or not clause_text.strip():
            return []

        detected_risks: List[Dict[str, Any]] = []

        for r_type, config in RISK_PATTERNS.items():
            # Filter explicit negation of automatic renewal to eliminate false positives
            if r_type == "automatic_renewal":
                if re.search(r"\b(without|no|not\s+have|will\s+not|never)\s+(?:any\s+)?automatic\s+renewal\b", clause_text, re.IGNORECASE):
                    continue

            match = re.search(config["pattern"], clause_text, re.IGNORECASE)
            if match:
                evidence_quote = match.group(0).strip()
                risk_item = {
                    "risk_type": r_type,
                    "severity": config["default_severity"],
                    "confidence": 0.88,
                    "description": config["description"],
                    "evidence": evidence_quote
                }
                if validate_risk_flag(risk_item, clause_text):
                    detected_risks.append(risk_item)

        return detected_risks

    def analyze_and_store_contract_risks(
        self,
        db: Session,
        contract_id: str
    ) -> List[RiskFlag]:
        """
        Scan all contract clauses, detect risks, and persist RiskFlag ORM models.
        """
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError(f"Contract with id '{contract_id}' not found.")

        clauses = db.query(Clause).filter(Clause.contract_id == contract_id).all()
        if not clauses:
            from backend.app.services.clause_classifier import get_clause_classifier
            try:
                clauses = get_clause_classifier().extract_and_store_clauses(db=db, contract_id=contract_id)
            except Exception:
                clauses = []
        if not clauses:
            return []

        db_risks: List[RiskFlag] = []
        seen_keys = set()

        for cl in clauses:
            detected = self.analyze_clause_text(cl.text, cl.clause_type)
            for r_dict in detected:
                key = (r_dict["risk_type"], cl.id)
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                risk_rec = RiskFlag(
                    contract_id=contract_id,
                    clause_id=cl.id,
                    risk_type=r_dict["risk_type"],
                    severity=r_dict["severity"],
                    description=r_dict["description"],
                    evidence=r_dict["evidence"],
                    confidence=r_dict["confidence"]
                )
                db_risks.append(risk_rec)

        if db_risks:
            # Idempotent replacement for contract risks
            db.query(RiskFlag).filter(RiskFlag.contract_id == contract_id).delete()
            db.add_all(db_risks)
            db.commit()

        return db_risks


# Default singleton instance
_risk_analyzer = RiskAnalyzer()


def get_risk_analyzer() -> RiskAnalyzer:
    """Return default RiskAnalyzer instance."""
    return _risk_analyzer
