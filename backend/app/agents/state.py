import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AgentState:
    """Internal working state container for an agent execution session."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    contract_id: Optional[str] = None
    contract_ids: List[str] = field(default_factory=list)
    conversation_id: Optional[str] = None
    max_steps: int = 5
    current_step: int = 0
    tools_called: List[str] = field(default_factory=list)
    tool_history: List[Dict[str, Any]] = field(default_factory=list)
    collected_evidence: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    is_sufficient: bool = False
    final_answer: Optional[str] = None
    summary: Optional[str] = None
    confidence: str = "MEDIUM"
    limitations: List[str] = field(default_factory=list)

    def record_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        observation: str,
        duration_ms: float,
        success: bool,
        evidence: Optional[List[Dict[str, Any]]] = None
    ):
        """Append an execution step to tool history and accumulate evidence."""
        self.current_step += 1
        if tool_name not in self.tools_called:
            self.tools_called.append(tool_name)

        step_record = {
            "step": self.current_step,
            "tool": tool_name,
            "arguments": arguments,
            "observation": observation,
            "duration_ms": round(duration_ms, 2),
            "success": success
        }
        self.tool_history.append(step_record)

        if evidence:
            for item in evidence:
                # Ensure unique evidence items based on chunk_id or (contract_id, page, text snippet)
                item_key = (
                    item.get("chunk_id") or 
                    (item.get("contract_id"), item.get("page_number") or item.get("page_start"), (item.get("text") or item.get("snippet") or "")[:50])
                )
                existing_keys = {
                    e.get("chunk_id") or 
                    (e.get("contract_id"), e.get("page_number") or e.get("page_start"), (e.get("text") or e.get("snippet") or "")[:50])
                    for e in self.collected_evidence
                }
                if item_key not in existing_keys:
                    self.collected_evidence.append(item)
