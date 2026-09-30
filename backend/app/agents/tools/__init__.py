from typing import Dict, List
from backend.app.agents.tools.base import BaseTool
from backend.app.agents.tools.search_tool import SearchContractTool
from backend.app.agents.tools.contract_tool import GetContractTool
from backend.app.agents.tools.clause_tool import GetClausesTool
from backend.app.agents.tools.entity_tool import GetEntitiesTool
from backend.app.agents.tools.obligation_tool import GetObligationsTool
from backend.app.agents.tools.risk_tool import GetRisksTool, AnalyzeRiskTool
from backend.app.agents.tools.graph_tool import QueryKnowledgeGraphTool
from backend.app.agents.tools.source_tool import RetrieveSourceTool
from backend.app.agents.tools.comparison_tool import CompareContractsTool


def get_all_tools() -> Dict[str, BaseTool]:
    """Instantiate and return mapping of tool_name -> BaseTool instance."""
    tools: List[BaseTool] = [
        SearchContractTool(),
        GetContractTool(),
        GetClausesTool(),
        GetEntitiesTool(),
        GetObligationsTool(),
        GetRisksTool(),
        AnalyzeRiskTool(),
        QueryKnowledgeGraphTool(),
        RetrieveSourceTool(),
        CompareContractsTool()
    ]
    return {t.name: t for t in tools}


__all__ = [
    "BaseTool",
    "SearchContractTool",
    "GetContractTool",
    "GetClausesTool",
    "GetEntitiesTool",
    "GetObligationsTool",
    "GetRisksTool",
    "AnalyzeRiskTool",
    "QueryKnowledgeGraphTool",
    "RetrieveSourceTool",
    "CompareContractsTool",
    "get_all_tools"
]
