from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.agents.tools.base import BaseTool, ToolResult
from backend.app.models.models import Contract, Entity
from backend.app.services.extractor import get_entity_extractor


class GetEntitiesTool(BaseTool):
    """Tool for retrieving extracted named entities (companies, persons, jurisdictions, dates, monetary amounts)."""
    name = "get_entities"
    description = (
        "Retrieve named entities extracted from a contract. "
        "Can be filtered by entity_type: COMPANY, PERSON, JURISDICTION, DATE, MONETARY_AMOUNT, ORGANIZATION."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "contract_id": {
                "type": "string",
                "description": "The UUID of the contract."
            },
            "entity_type": {
                "type": "string",
                "description": "Optional category of entity (e.g., 'COMPANY', 'JURISDICTION', 'PERSON')."
            }
        },
        "required": ["contract_id"]
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            self.validate_args(kwargs)
            contract_id = kwargs.get("contract_id")
            entity_type = kwargs.get("entity_type")

            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                return ToolResult(
                    success=False,
                    data=[],
                    error=f"Contract with id '{contract_id}' not found.",
                    summary_for_agent=f"Contract '{contract_id}' not found."
                )

            entities = db.query(Entity).filter(Entity.contract_id == contract_id).all()
            if not entities:
                # Trigger extraction on demand if not yet populated
                try:
                    extractor = get_entity_extractor()
                    entities = extractor.extract_and_store_entities(db=db, contract_id=contract_id)
                except Exception:
                    entities = []

            if entity_type:
                clean_type = entity_type.strip().upper()
                entities = [e for e in entities if e.entity_type.upper() == clean_type]

            if not entities:
                type_msg = f" of type '{entity_type}'" if entity_type else ""
                return ToolResult(
                    success=True,
                    data=[],
                    evidence=[],
                    summary_for_agent=f"No entities{type_msg} found in contract '{contract.name}'."
                )

            data = []
            evidence = []
            for e in entities:
                item_dict = {
                    "entity_id": e.id,
                    "contract_id": e.contract_id,
                    "entity_type": e.entity_type,
                    "name": e.name,
                    "normalized_name": e.normalized_name,
                    "confidence": round(e.confidence, 4)
                }
                data.append(item_dict)
                evidence.append({
                    "contract_id": e.contract_id,
                    "contract_name": contract.name,
                    "source_location": f"Contract Entities ({e.entity_type})",
                    "snippet": f"{e.entity_type}: {e.name} (Canonical: {e.normalized_name})",
                    "relevance_score": e.confidence
                })

            summary = f"Retrieved {len(entities)} entity/entities for '{contract.name}': " + ", ".join(
                f"{e.name} ({e.entity_type})" for e in entities[:5]
            )
            return ToolResult(
                success=True,
                data=data,
                evidence=evidence,
                summary_for_agent=summary
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=[],
                error=f"GetEntitiesTool failed: {str(e)}",
                summary_for_agent=f"Error retrieving entities: {str(e)}"
            )
