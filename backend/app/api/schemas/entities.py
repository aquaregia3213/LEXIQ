from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class EntityItemResponse(BaseModel):
    """Extracted contract entity schema."""
    entity_id: str
    id: str
    contract_id: str
    entity_type: str
    text: str
    name: str
    normalized_value: Optional[str] = None
    normalized_name: Optional[str] = None
    confidence: float
    source_location: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
