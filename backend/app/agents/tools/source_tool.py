from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.agents.tools.base import BaseTool, ToolResult
from backend.app.models.models import Contract, Chunk


class RetrieveSourceTool(BaseTool):
    """Tool for retrieving verified original page text or chunk context from a contract."""
    name = "retrieve_source"
    description = (
        "Retrieve the exact original document text for a specific page number or chunk ID. "
        "Essential for verifying claims, inspecting context, and confirming evidence quotes."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "contract_id": {
                "type": "string",
                "description": "The UUID of the contract."
            },
            "page_number": {
                "type": "integer",
                "description": "The specific page number to retrieve."
            },
            "chunk_id": {
                "type": "string",
                "description": "Optional specific chunk UUID to look up directly."
            }
        },
        "required": ["contract_id"]
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            self.validate_args(kwargs)
            contract_id = kwargs.get("contract_id")
            page_number = kwargs.get("page_number")
            chunk_id = kwargs.get("chunk_id")

            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Contract '{contract_id}' not found.",
                    summary_for_agent=f"Contract '{contract_id}' does not exist."
                )

            query = db.query(Chunk).filter(Chunk.contract_id == contract_id)

            if chunk_id:
                query = query.filter(Chunk.id == chunk_id)
            elif page_number is not None:
                query = query.filter((Chunk.page_start <= page_number) & (Chunk.page_end >= page_number))

            chunks = query.order_by(Chunk.chunk_index.asc()).all()
            if not chunks:
                loc_desc = f"page {page_number}" if page_number else f"chunk {chunk_id}"
                return ToolResult(
                    success=True,
                    data=[],
                    evidence=[],
                    summary_for_agent=f"No source text found for {loc_desc} in contract '{contract.name}'."
                )

            combined_text = "\n\n".join(c.text for c in chunks)
            evidence = []
            for c in chunks:
                evidence.append({
                    "contract_id": contract.id,
                    "contract_name": contract.name,
                    "chunk_id": c.id,
                    "page_number": c.page_start,
                    "section": c.metadata_json.get("section", "General") if c.metadata_json else "General",
                    "source_location": f"Page {c.page_start}",
                    "snippet": c.text,
                    "relevance_score": 1.0
                })

            summary = f"Retrieved source text for {len(chunks)} chunk(s) from '{contract.name}' (Page {chunks[0].page_start})."
            return ToolResult(
                success=True,
                data={
                    "contract_id": contract.id,
                    "contract_name": contract.name,
                    "page_number": page_number,
                    "chunk_count": len(chunks),
                    "text": combined_text
                },
                evidence=evidence,
                summary_for_agent=summary
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"RetrieveSourceTool failed: {str(e)}",
                summary_for_agent=f"Error retrieving source: {str(e)}"
            )
