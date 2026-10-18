from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    """Input payload for agent query endpoint."""
    question: str = Field(..., min_length=1, description="The legal question or analysis request.")
    contract_id: Optional[str] = Field(None, description="Optional target contract UUID.")
    contract_ids: Optional[List[str]] = Field(default_factory=list, description="Optional list of contract UUIDs for comparison or cross-contract queries.")
    conversation_id: Optional[str] = Field(None, description="Optional conversation/session ID.")
    user_id: Optional[str] = Field(None, description="Optional authenticated user UUID for multi-tenant isolation.")
    max_steps: Optional[int] = Field(default=5, ge=1, le=10, description="Maximum number of tool execution steps.")


class AgentSourceCitation(BaseModel):
    """Verifiable source reference cited by the agent."""
    contract_id: Optional[str] = None
    contract_name: Optional[str] = None
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    source_location: Optional[str] = None
    snippet: Optional[str] = None
    relevance_score: Optional[float] = None


class AgentFinding(BaseModel):
    """Specific factual or analytical finding extracted from contract evidence."""
    category: str = Field(..., description="Category of finding (clause, risk, obligation, entity, metadata).")
    fact: str = Field(..., description="The substantive fact or conclusion.")
    contract_id: Optional[str] = None
    contract_name: Optional[str] = None
    page_number: Optional[int] = None
    source_reference: Optional[str] = None


class AgentQueryResponse(BaseModel):
    """Standardized output schema for Agentic AI contract analysis."""
    answer: str = Field(..., description="The comprehensive grounded answer.")
    summary: str = Field(..., description="Concise executive summary.")
    findings: List[AgentFinding] = Field(default_factory=list, description="Key factual findings.")
    sources: List[AgentSourceCitation] = Field(default_factory=list, description="Verified source evidence citations.")
    tools_used: List[str] = Field(default_factory=list, description="List of tools invoked during the reasoning process.")
    confidence: str = Field(default="MEDIUM", description="Confidence level: HIGH, MEDIUM, or LOW.")
    limitations: List[str] = Field(default_factory=list, description="Any boundaries, caveats, or missing evidence disclosures.")


class ToolExecutionRequest(BaseModel):
    """Payload for authenticated tool execution by workflow orchestrators (e.g. Langflow)."""
    tool_name: str = Field(..., description="Name of the approved LEXIQ agent tool to execute.")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Key-value arguments conforming to the tool's schema.")
    contract_id: Optional[str] = Field(None, description="Optional target contract UUID to enforce multi-tenant authorization.")
    user_id: Optional[str] = Field(None, description="Optional requesting user UUID for tenant boundary checks.")


class ToolExecutionResponse(BaseModel):
    """Standardized response schema returned by the tool execution endpoint."""
    success: bool = Field(..., description="Whether the tool executed successfully.")
    tool_name: str = Field(..., description="Name of the executed tool.")
    data: Any = Field(None, description="Structured tool output data.")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="List of evidence citations extracted by the tool.")
    summary_for_agent: str = Field(..., description="Compact natural-language summary suitable for agent consumption.")
    error: Optional[str] = Field(None, description="Error message if execution failed.")
