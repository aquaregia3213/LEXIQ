from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class RiskItemResponse(BaseModel):
    """Identified potential risk flag schema."""
    risk_id: str
    id: str
    contract_id: str
    clause_id: Optional[str] = None
    risk_type: str
    severity: str
    confidence: float
    explanation: str
    description: str
    evidence: Optional[str] = None
    source_location: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class RiskAnalysisResponseV1(BaseModel):
    """Risk analysis response with explicit legal safety disclaimer."""
    contract_id: str
    risk_count: int
    disclaimer: str
    risks: List[RiskItemResponse]
