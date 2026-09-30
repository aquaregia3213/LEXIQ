from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class GraphNodeV1(BaseModel):
    """Knowledge Graph entity or concept node."""
    id: str
    label: str
    name: Optional[str] = None
    type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")


class GraphRelationshipV1(BaseModel):
    """Directed Knowledge Graph relationship edge between nodes."""
    source: str
    target: str
    type: str
    properties: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")


class GraphResponseV1(BaseModel):
    """Knowledge Graph subgraph response formatted for frontend graph visualizers."""
    contract_id: str
    node_count: int
    relationship_count: int
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    edges: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)
