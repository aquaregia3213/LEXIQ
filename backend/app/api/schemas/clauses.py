from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ClauseItemResponse(BaseModel):
    """Extracted and classified contract clause schema."""
    clause_id: str
    id: str
    contract_id: str
    document_id: Optional[str] = None
    clause_type: str
    text: str
    confidence: float
    page_number: int = 1
    source_location: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
