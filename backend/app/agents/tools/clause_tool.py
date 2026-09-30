from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.agents.tools.base import BaseTool, ToolResult
from backend.app.models.models import Contract, Clause
from backend.app.services.clause_classifier import get_clause_classifier


class GetClausesTool(BaseTool):
    """Tool for retrieving classified clauses from a contract (Termination, Liability, etc.)."""
    name = "get_clauses"
    description = (
        "Retrieve extracted and classified legal clauses for a contract. "
        "Can be filtered by clause type: Termination, Liability, Indemnification, Confidentiality, "
        "Payment, Intellectual Property, Data Protection, Non-Compete, Non-Solicitation, Renewal, "
        "Governing Law, Dispute Resolution."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "contract_id": {
                "type": "string",
                "description": "The UUID of the contract."
            },
            "clause_type": {
                "type": "string",
                "description": "Optional category of clause to filter by (e.g., 'Termination', 'Liability', 'Renewal')."
            }
        },
        "required": ["contract_id"]
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            self.validate_args(kwargs)
            contract_id = kwargs.get("contract_id")
            clause_type = kwargs.get("clause_type")

            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                return ToolResult(
                    success=False,
                    data=[],
                    error=f"Contract with id '{contract_id}' not found.",
                    summary_for_agent=f"Contract '{contract_id}' not found."
                )

            clauses = db.query(Clause).filter(Clause.contract_id == contract_id).all()
            if not clauses:
                # Trigger extraction on demand if not yet populated
                try:
                    classifier = get_clause_classifier()
                    clauses = classifier.extract_and_store_clauses(db=db, contract_id=contract_id)
                except Exception:
                    clauses = []

            if clause_type:
                clean_type = clause_type.strip().lower()
                clauses = [c for c in clauses if clean_type in c.clause_type.lower()]

            if not clauses:
                type_msg = f" of type '{clause_type}'" if clause_type else ""
                return ToolResult(
                    success=True,
                    data=[],
                    evidence=[],
                    summary_for_agent=f"No clauses{type_msg} found in contract '{contract.name}'."
                )

            data = []
            evidence = []
            for c in clauses:
                loc = f"Page {c.page_number}, Clause: {c.clause_type}"
                item_dict = {
                    "clause_id": c.id,
                    "contract_id": c.contract_id,
                    "clause_type": c.clause_type,
                    "text": c.text,
                    "page_number": c.page_number,
                    "confidence": round(c.confidence, 4)
                }
                data.append(item_dict)
                evidence.append({
                    "contract_id": c.contract_id,
                    "contract_name": contract.name,
                    "document_id": c.document_id,
                    "clause_id": c.id,
                    "page_number": c.page_number,
                    "section": c.clause_type,
                    "source_location": loc,
                    "snippet": c.text,
                    "relevance_score": c.confidence
                })

            summary = f"Retrieved {len(clauses)} clause(s) for '{contract.name}'" + (f" matching '{clause_type}'." if clause_type else ".")
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
                error=f"GetClausesTool failed: {str(e)}",
                summary_for_agent=f"Error retrieving clauses: {str(e)}"
            )
