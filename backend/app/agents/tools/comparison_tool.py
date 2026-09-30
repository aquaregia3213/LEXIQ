from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.agents.tools.base import BaseTool, ToolResult
from backend.app.models.models import Contract, Clause
from backend.app.services.clause_classifier import get_clause_classifier


class CompareContractsTool(BaseTool):
    """Tool for comparing specific clause provisions or risk terms across two contracts."""
    name = "compare_contracts"
    description = (
        "Compare specific clause types (e.g., Termination, Liability, Indemnification, Renewal, "
        "Governing Law) across two distinct contracts. Identifies textual differences and page locations."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "contract_id_a": {
                "type": "string",
                "description": "UUID of the first contract."
            },
            "contract_id_b": {
                "type": "string",
                "description": "UUID of the second contract."
            },
            "clause_type": {
                "type": "string",
                "description": "Clause category to compare (e.g., 'Termination', 'Liability', 'Confidentiality')."
            }
        },
        "required": ["contract_id_a", "contract_id_b", "clause_type"]
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            self.validate_args(kwargs)
            id_a = kwargs.get("contract_id_a")
            id_b = kwargs.get("contract_id_b")
            clause_type = kwargs.get("clause_type", "").strip()

            c_a = db.query(Contract).filter(Contract.id == id_a).first()
            c_b = db.query(Contract).filter(Contract.id == id_b).first()

            if not c_a or not c_b:
                missing = []
                if not c_a:
                    missing.append(f"Contract A '{id_a}'")
                if not c_b:
                    missing.append(f"Contract B '{id_b}'")
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Comparison failed: {', '.join(missing)} not found.",
                    summary_for_agent=f"Could not find {', '.join(missing)}."
                )

            classifier = get_clause_classifier()

            def get_contract_clauses(c_id):
                cls = db.query(Clause).filter(Clause.contract_id == c_id).all()
                if not cls:
                    try:
                        cls = classifier.extract_and_store_clauses(db=db, contract_id=c_id)
                    except Exception:
                        cls = []
                return [c for c in cls if clause_type.lower() in c.clause_type.lower()]

            clauses_a = get_contract_clauses(id_a)
            clauses_b = get_contract_clauses(id_b)

            text_a = "\n\n".join(c.text for c in clauses_a) if clauses_a else "Not explicitly specified."
            text_b = "\n\n".join(c.text for c in clauses_b) if clauses_b else "Not explicitly specified."
            page_a = clauses_a[0].page_number if clauses_a else None
            page_b = clauses_b[0].page_number if clauses_b else None

            is_different = text_a.strip().lower() != text_b.strip().lower()

            evidence = []
            if clauses_a:
                evidence.append({
                    "contract_id": id_a,
                    "contract_name": c_a.name,
                    "page_number": page_a,
                    "section": clause_type,
                    "source_location": f"Page {page_a}, Clause: {clause_type}",
                    "snippet": f"In {c_a.name}: {text_a}",
                    "relevance_score": 0.95
                })
            if clauses_b:
                evidence.append({
                    "contract_id": id_b,
                    "contract_name": c_b.name,
                    "page_number": page_b,
                    "section": clause_type,
                    "source_location": f"Page {page_b}, Clause: {clause_type}",
                    "snippet": f"In {c_b.name}: {text_b}",
                    "relevance_score": 0.95
                })

            if is_different:
                evidence.append({
                    "contract_id": id_a,
                    "contract_name": f"{c_a.name} vs {c_b.name}",
                    "page_number": page_a or 1,
                    "section": "Contract Comparison",
                    "source_location": f"{clause_type} Comparison",
                    "snippet": f"Identified differences in {clause_type} provisions: {c_a.name} specifies notice/terms differing from {c_b.name}.",
                    "relevance_score": 0.98
                })

            comparison_data = {
                "clause_type": clause_type,
                "contract_a": {
                    "id": id_a,
                    "name": c_a.name,
                    "clause_text": text_a,
                    "page_number": page_a
                },
                "contract_b": {
                    "id": id_b,
                    "name": c_b.name,
                    "clause_text": text_b,
                    "page_number": page_b
                },
                "provisions_differ": is_different
            }

            summary = (
                f"Compared '{clause_type}' between '{c_a.name}' and '{c_b.name}'. "
                f"Provisions are {'different' if is_different else 'identical'}."
            )

            return ToolResult(
                success=True,
                data=comparison_data,
                evidence=evidence,
                summary_for_agent=summary
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"CompareContractsTool failed: {str(e)}",
                summary_for_agent=f"Error comparing contracts: {str(e)}"
            )
