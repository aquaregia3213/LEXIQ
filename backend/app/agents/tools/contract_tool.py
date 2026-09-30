from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.agents.tools.base import BaseTool, ToolResult
from backend.app.models.models import Contract, Document, Chunk


class GetContractTool(BaseTool):
    """Tool for retrieving contract metadata, status, or listing all registered contracts."""
    name = "get_contract"
    description = (
        "Retrieve contract metadata including name, type, status, page count, and chunk count. "
        "Can also list all contracts in the repository if contract_id is omitted or set to 'all'."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "contract_id": {
                "type": "string",
                "description": "Optional UUID or name of the contract. If omitted or 'all', lists all contracts."
            }
        }
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            contract_id = kwargs.get("contract_id")

            if not contract_id or contract_id.lower() == "all":
                contracts = db.query(Contract).order_by(Contract.created_at.desc()).all()
                data = [
                    {
                        "contract_id": c.id,
                        "name": c.name,
                        "contract_type": c.contract_type,
                        "status": c.status,
                        "created_at": str(c.created_at)
                    }
                    for c in contracts
                ]
                summary = f"Retrieved {len(data)} contract(s) from the repository."
                return ToolResult(
                    success=True,
                    data=data,
                    evidence=[],
                    summary_for_agent=summary
                )

            # Query specific contract by id or name
            contract = db.query(Contract).filter(
                (Contract.id == contract_id) | (Contract.name.ilike(f"%{contract_id}%"))
            ).first()

            if not contract:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Contract '{contract_id}' not found.",
                    summary_for_agent=f"Contract with identifier '{contract_id}' does not exist in the repository."
                )

            doc_count = db.query(Document).filter(Document.contract_id == contract.id).count()
            chunk_count = db.query(Chunk).filter(Chunk.contract_id == contract.id).count()

            contract_data = {
                "contract_id": contract.id,
                "name": contract.name,
                "contract_type": contract.contract_type,
                "status": contract.status,
                "document_count": doc_count,
                "chunk_count": chunk_count,
                "created_at": str(contract.created_at)
            }

            evidence = [{
                "contract_id": contract.id,
                "contract_name": contract.name,
                "source_location": "Contract Metadata Record",
                "snippet": f"Contract Name: {contract.name}, Type: {contract.contract_type}, Status: {contract.status}"
            }]

            summary = f"Contract '{contract.name}' (ID: {contract.id}) is of type '{contract.contract_type}' with {chunk_count} chunk(s)."
            return ToolResult(
                success=True,
                data=contract_data,
                evidence=evidence,
                summary_for_agent=summary
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"GetContractTool failed: {str(e)}",
                summary_for_agent=f"Error retrieving contract: {str(e)}"
            )
