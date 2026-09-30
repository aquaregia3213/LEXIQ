from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.agents.tools.base import BaseTool, ToolResult
from backend.app.services.graph import get_graph_service


class QueryKnowledgeGraphTool(BaseTool):
    """Tool for traversing relational knowledge graph: companies, jurisdictions, and contract subgraphs."""
    name = "query_knowledge_graph"
    description = (
        "Traverse the contract Knowledge Graph to find cross-contract relationships. "
        "Supported query_types: 'by_company' (find contracts involving a company), "
        "'by_jurisdiction' (find contracts governed by a state/country), or "
        "'contract_subgraph' (retrieve all linked parties, clauses, and obligations for a contract)."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "enum": ["by_company", "by_jurisdiction", "contract_subgraph"],
                "description": "Type of graph traversal: 'by_company', 'by_jurisdiction', or 'contract_subgraph'."
            },
            "target": {
                "type": "string",
                "description": "The name of the company, jurisdiction, or contract UUID."
            }
        },
        "required": ["query_type", "target"]
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            self.validate_args(kwargs)
            query_type = kwargs.get("query_type")
            target = kwargs.get("target", "").strip()

            graph_service = get_graph_service()

            if query_type == "by_company":
                results = graph_service.query_contracts_by_company(target)
                evidence = []
                for c in results:
                    evidence.append({
                        "contract_id": c.get("id"),
                        "contract_name": c.get("name"),
                        "source_location": "Knowledge Graph (Company -> Contract)",
                        "snippet": f"Company '{target}' is a party/signatory to Contract '{c.get('name')}' (Type: {c.get('type')})",
                        "relevance_score": 0.95
                    })
                summary = f"Graph query found {len(results)} contract(s) involving company '{target}'."
                return ToolResult(
                    success=True,
                    data=results,
                    evidence=evidence,
                    summary_for_agent=summary
                )

            elif query_type == "by_jurisdiction":
                results = graph_service.query_contracts_by_jurisdiction(target)
                evidence = []
                for c in results:
                    evidence.append({
                        "contract_id": c.get("id"),
                        "contract_name": c.get("name"),
                        "source_location": "Knowledge Graph (Jurisdiction -> Contract)",
                        "snippet": f"Contract '{c.get('name')}' is governed by the laws/jurisdiction of '{target}'",
                        "relevance_score": 0.95
                    })
                summary = f"Graph query found {len(results)} contract(s) governed by jurisdiction '{target}'."
                return ToolResult(
                    success=True,
                    data=results,
                    evidence=evidence,
                    summary_for_agent=summary
                )

            elif query_type == "contract_subgraph":
                subgraph = graph_service.get_contract_graph(target)
                if not subgraph.get("nodes"):
                    # Attempt sync if not yet in graph
                    try:
                        subgraph = graph_service.sync_contract_to_graph(db=db, contract_id=target)
                    except Exception:
                        pass

                nodes = subgraph.get("nodes", [])
                edges = subgraph.get("edges", [])

                evidence = []
                for node in nodes:
                    if node.get("label") in ("Company", "Jurisdiction", "Obligation", "Risk"):
                        evidence.append({
                            "contract_id": target,
                            "source_location": f"Knowledge Graph ({node.get('label')})",
                            "snippet": f"Linked {node.get('label')}: {node.get('name') or node.get('description') or node.get('type')}",
                            "relevance_score": 0.90
                        })

                summary = f"Retrieved subgraph for contract '{target}' with {len(nodes)} node(s) and {len(edges)} relationship(s)."
                return ToolResult(
                    success=True,
                    data=subgraph,
                    evidence=evidence,
                    summary_for_agent=summary
                )

            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unsupported query_type '{query_type}'. Use 'by_company', 'by_jurisdiction', or 'contract_subgraph'.",
                    summary_for_agent=f"Invalid query_type '{query_type}'."
                )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"QueryKnowledgeGraphTool failed: {str(e)}",
                summary_for_agent=f"Error executing graph traversal: {str(e)}"
            )
