from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.agents.tools.base import BaseTool, ToolResult
from backend.app.services.search import get_search_service


class SearchContractTool(BaseTool):
    """Tool for searching contract text chunks using semantic vector search and section filters."""
    name = "search_contract"
    description = (
        "Perform semantic similarity search over contract text chunks using dense embeddings. "
        "Useful for locating specific terms, questions, notice periods, or clauses."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query or phrase to search for."
            },
            "contract_id": {
                "type": "string",
                "description": "Optional UUID of a specific contract to scope the search to."
            },
            "section": {
                "type": "string",
                "description": "Optional section heading to filter by (e.g., 'Termination', 'Liability', 'Renewal')."
            },
            "top_k": {
                "type": "integer",
                "default": 4,
                "description": "Maximum number of relevant chunks to retrieve (default: 4)."
            }
        },
        "required": ["query"]
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            self.validate_args(kwargs)
            query = kwargs.get("query", "").strip()
            contract_id = kwargs.get("contract_id")
            section = kwargs.get("section")
            top_k = kwargs.get("top_k", 4)

            search_service = get_search_service()
            results = search_service.semantic_search(
                db=db,
                query=query,
                contract_id=contract_id,
                section=section,
                top_k=top_k,
                min_score=0.0
            )

            if not results:
                return ToolResult(
                    success=True,
                    data=[],
                    evidence=[],
                    summary_for_agent=f"No matching contract chunks found for query '{query}'."
                )

            evidence = []
            for item in results:
                p_start = item.get("page_start", 1)
                p_end = item.get("page_end", 1)
                loc = f"Page {p_start}" if p_start == p_end else f"Pages {p_start}-{p_end}"
                sec = item.get("section", "General")
                if sec and sec != "General":
                    loc += f", Section: {sec}"

                evidence.append({
                    "contract_id": item.get("contract_id"),
                    "contract_name": item.get("contract_name"),
                    "document_id": item.get("document_id"),
                    "chunk_id": item.get("chunk_id"),
                    "page_number": p_start,
                    "section": sec,
                    "source_location": loc,
                    "snippet": item.get("text"),
                    "relevance_score": item.get("similarity_score")
                })

            summary = f"Found {len(results)} relevant chunk(s) for '{query}' across contracts: " + ", ".join(
                {r.get('contract_name', 'Contract') for r in results}
            )
            return ToolResult(
                success=True,
                data=results,
                evidence=evidence,
                summary_for_agent=summary
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=[],
                error=f"SearchContractTool failed: {str(e)}",
                summary_for_agent=f"Error executing search for query '{kwargs.get('query', '')}': {str(e)}"
            )
