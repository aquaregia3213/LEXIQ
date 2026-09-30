from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ObligationItemResponse(BaseModel):
    """Extracted contractual obligation schema."""
    obligation_id: str
    id: str
    contract_id: str
    obligation: str
    description: str
    responsible_party: Optional[str] = None
    party: Optional[str] = None
    deadline: Optional[str] = None
    confidence: float
    source_location: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
