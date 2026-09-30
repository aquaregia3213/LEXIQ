from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from sqlalchemy.orm import Session


@dataclass
class ToolResult:
    """Standardized output container returned by every agent tool."""
    success: bool
    data: Any
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    summary_for_agent: str = ""


class BaseTool(ABC):
    """Abstract base class for all LEXIQ agent tools."""
    name: str = ""
    description: str = ""
    parameters_schema: Dict[str, Any] = {}

    def get_openai_tool_definition(self) -> Dict[str, Any]:
        """Convert tool description and JSON Schema into standard function-calling definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        }

    def validate_args(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Basic validation checking for required properties defined in parameters_schema."""
        required_props = self.parameters_schema.get("required", [])
        for prop in required_props:
            if prop not in kwargs or kwargs[prop] is None:
                raise ValueError(f"Missing required parameter '{prop}' for tool '{self.name}'.")
        return kwargs

    @abstractmethod
    def execute(self, db: Session, **kwargs) -> ToolResult:
        """Execute the tool logic using existing backend services and database session."""
        pass
