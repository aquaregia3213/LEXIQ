import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.models import Contract, Chunk, Entity

VALID_ENTITY_TYPES = {
    "COMPANY",
    "PERSON",
    "ORGANIZATION",
    "DATE",
    "MONETARY_AMOUNT",
    "JURISDICTION"
}

# Regex patterns for rule-based entity extraction
REGEX_PATTERNS = {
    "COMPANY": r"\b([A-Z][A-Za-z0-9\&]+(?:\s+[A-Z][A-Za-z0-9\&]+)*\s+(?:Inc\.?|Incorporated|Corp\.?|Corporation|LLC|L\.L\.C\.?|Ltd\.?|Limited|GmbH|Co\.?))\b",
    "JURISDICTION": r"\b(?:[Gg]overned\s+by\s+the\s+laws\s+of|[Ll]aws\s+of|[Cc]ourts\s+of|[Jj]urisdiction\s+of|[Ss]tate\s+of|[Cc]ommonwealth\s+of|payable\s+in|located\s+in)\s+(?:the\s+)?(?:State\s+of\s+|Commonwealth\s+of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
    "DATE": r"\b(?:\d{4}-\d{2}-\d{2}|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})\b",
    "MONETARY_AMOUNT": r"(?:\$\s?[\d,]+(?:\.\d{2})?(?:\s*(?:USD|EUR|GBP|Dollars))?|[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP|Dollars))",
    "PERSON": r"\b(?:By|Name|Signatory|Attn|Title|BY|NAME):\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)\b",
    "ORGANIZATION": r"\b([A-Z][A-Za-z0-9\&]+(?:\s+[A-Z][A-Za-z0-9\&]+)*\s+(?:Department|Commission|Authority|Board|Association|Foundation))\b"
}


def normalize_entity_name(entity_type: str, raw_name: str) -> str:
    """Normalize extracted entity names into canonical formats."""
    clean_name = raw_name.strip()
    if not clean_name:
        return clean_name

    e_type = entity_type.upper()

    if e_type == "COMPANY":
        norm = clean_name
        norm = re.sub(r",\s*(Inc\.?|Corp\.?|Ltd\.?|LLC|Co\.?)$", r" \1", norm, flags=re.IGNORECASE)
        norm = re.sub(r"\bInc\.?$", "Incorporated", norm, flags=re.IGNORECASE)
        norm = re.sub(r"\bCorp\.?$", "Corporation", norm, flags=re.IGNORECASE)
        norm = re.sub(r"\bLtd\.?$", "Limited", norm, flags=re.IGNORECASE)
        norm = re.sub(r"\bLLC\.?$", "Limited Liability Company", norm, flags=re.IGNORECASE)
        norm = re.sub(r"\bCo\.?$", "Company", norm, flags=re.IGNORECASE)
        return norm.strip()

    elif e_type == "MONETARY_AMOUNT":
        clean_val = clean_name.replace("$", "").replace(",", "").strip()
        parts = clean_val.split()
        if parts:
            num_part = parts[0]
            curr = parts[1].upper() if len(parts) > 1 and parts[1].upper() in ("USD", "EUR", "GBP", "DOLLARS") else "USD"
            if curr == "DOLLARS":
                curr = "USD"
            return f"{num_part} {curr}"
        return clean_name.upper()

    elif e_type == "JURISDICTION":
        prefix_pattern = r"^(governed by the laws of|laws of|courts of|jurisdiction of|State of|Commonwealth of|payable in|located in)\s+(?:the\s+)?(?:State of\s+|Commonwealth of\s+)?"
        norm = re.sub(prefix_pattern, "", clean_name, flags=re.IGNORECASE)
        return norm.title().strip()

    elif e_type == "PERSON":
        prefix_pattern = r"^(By|Name|Signatory|Attn|Title):\s*"
        norm = re.sub(prefix_pattern, "", clean_name, flags=re.IGNORECASE)
        return norm.title().strip()

    return clean_name


def validate_entity(entity: Dict[str, Any], contract_text: str) -> bool:
    """
    Validate extracted entity model output before storing in database.
    Verifies entity type validity, non-empty name, confidence bounds, and source text inclusion.
    """
    entity_type = entity.get("entity_type", "").upper()
    name = entity.get("name", "").strip()
    confidence = entity.get("confidence", 1.0)

    # 1. Type validation
    if entity_type not in VALID_ENTITY_TYPES:
        return False

    # 2. Name validation
    if not name or len(name) > 255:
        return False

    # 3. Confidence validation
    if not (0.0 <= confidence <= 1.0):
        return False

    # 4. Source grounding validation: extracted entity name must exist in source contract text
    clean_text = contract_text.lower()
    clean_name = name.lower()

    # Strip prefixes for matching if needed
    clean_name = re.sub(r"^(by|name|signatory|attn):\s*", "", clean_name)

    if clean_name in clean_text:
        return True

    # Generic stop words that alone are insufficient to establish grounding
    generic_words = {"corp", "corp.", "inc", "inc.", "ltd", "ltd.", "llc", "co", "co.", "company", "corporation", "limited", "state", "of", "department", "commission"}
    substantive_words = [w for w in re.findall(r"\w+", clean_name) if w not in generic_words]

    if not substantive_words:
        return False

    return all(w in clean_text for w in substantive_words)


class EntityExtractor:
    """Service handling multi-type entity extraction, normalization, and validation."""

    def extract_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from plain text using hybrid pattern & NLP rules."""
        if not text or not text.strip():
            return []

        extracted: List[Dict[str, Any]] = []
        seen = set()

        for entity_type, pattern in REGEX_PATTERNS.items():
            flags = re.IGNORECASE if entity_type in ("DATE", "MONETARY_AMOUNT") else 0
            matches = re.finditer(pattern, text, flags)
            for match in matches:
                name_str = match.group(1) if match.groups() else match.group(0)
                name_str = name_str.strip()

                if not name_str:
                    continue

                key = (entity_type, name_str.lower())
                if key in seen:
                    continue
                seen.add(key)

                norm_name = normalize_entity_name(entity_type, name_str)

                item = {
                    "entity_type": entity_type,
                    "name": name_str,
                    "normalized_name": norm_name,
                    "confidence": 0.95
                }

                if validate_entity(item, text):
                    extracted.append(item)

        return extracted

    def extract_and_store_entities(
        self,
        db: Session,
        contract_id: str
    ) -> List[Entity]:
        """
        Execute entity extraction on contract document chunks and persist validated Entity models.
        """
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError(f"Contract with id '{contract_id}' not found.")

        chunks = db.query(Chunk).filter(Chunk.contract_id == contract_id).all()
        if not chunks:
            return []

        full_text = "\n\n".join(chunk.text for chunk in chunks)
        raw_entities = self.extract_from_text(full_text)

        db_entities = []
        seen_keys = set()

        for ent_dict in raw_entities:
            key = (ent_dict["entity_type"], ent_dict["normalized_name"].lower())
            if key in seen_keys:
                continue
            seen_keys.add(key)

            entity_rec = Entity(
                contract_id=contract_id,
                entity_type=ent_dict["entity_type"],
                name=ent_dict["name"],
                normalized_name=ent_dict["normalized_name"],
                confidence=ent_dict["confidence"]
            )
            db_entities.append(entity_rec)

        if db_entities:
            # Delete existing entities for idempotent reprocessing
            db.query(Entity).filter(Entity.contract_id == contract_id).delete()
            db.add_all(db_entities)
            db.commit()

        return db_entities


# Singleton instance
_entity_extractor = EntityExtractor()


def get_entity_extractor() -> EntityExtractor:
    """Return default EntityExtractor instance."""
    return _entity_extractor
