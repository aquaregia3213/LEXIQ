from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.agents.tools.base import BaseTool, ToolResult
from backend.app.models.models import Contract, Obligation
from backend.app.services.obligation_extractor import get_obligation_extractor


class GetObligationsTool(BaseTool):
    """Tool for retrieving contractual obligations, responsible parties, and deadlines."""
    name = "get_obligations"
    description = (
        "Retrieve obligations, covenants, and commitments defined in a contract. "
        "Can be filtered by responsible party (e.g., 'Vendor', 'Customer', 'Acme')."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "contract_id": {
                "type": "string",
                "description": "The UUID of the contract."
            },
            "party": {
                "type": "string",
                "description": "Optional name or role of the responsible party to filter by."
            }
        },
        "required": ["contract_id"]
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            self.validate_args(kwargs)
            contract_id = kwargs.get("contract_id")
            party_filter = kwargs.get("party")

            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                return ToolResult(
                    success=False,
                    data=[],
                    error=f"Contract with id '{contract_id}' not found.",
                    summary_for_agent=f"Contract '{contract_id}' not found."
                )

            obligations = db.query(Obligation).filter(Obligation.contract_id == contract_id).all()
            if not obligations:
                try:
                    extractor = get_obligation_extractor()
                    obligations = extractor.extract_and_store_obligations(db=db, contract_id=contract_id)
                except Exception:
                    obligations = []

            if party_filter:
                clean_p = party_filter.strip().lower()
                obligations = [o for o in obligations if o.party and clean_p in o.party.lower()]

            if not obligations:
                p_msg = f" for party '{party_filter}'" if party_filter else ""
                return ToolResult(
                    success=True,
                    data=[],
                    evidence=[],
                    summary_for_agent=f"No obligations{p_msg} found in contract '{contract.name}'."
                )

            data = []
            evidence = []
            for ob in obligations:
                item_dict = {
                    "obligation_id": ob.id,
                    "contract_id": ob.contract_id,
                    "description": ob.description,
                    "party": ob.party,
                    "deadline": ob.deadline,
                    "confidence": round(ob.confidence, 4)
                }
                data.append(item_dict)

                dl_str = f" (Deadline: {ob.deadline})" if ob.deadline else ""
                evidence.append({
                    "contract_id": ob.contract_id,
                    "contract_name": contract.name,
                    "source_location": f"Contract Obligations ({ob.party or 'General'})",
                    "snippet": f"Party: {ob.party or 'Unassigned'} -> {ob.description}{dl_str}",
                    "relevance_score": ob.confidence
                })

            summary = f"Retrieved {len(obligations)} obligation(s) for '{contract.name}'."
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
                error=f"GetObligationsTool failed: {str(e)}",
                summary_for_agent=f"Error retrieving obligations: {str(e)}"
            )
