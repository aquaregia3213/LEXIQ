from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class SearchRequestV1(BaseModel):
    """Payload for semantic search query."""
    query: str
    contract_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    contract_type: Optional[str] = None
    section: Optional[str] = None
    top_k: Optional[int] = 5
    min_score: Optional[float] = 0.0


class SearchResultItemV1(BaseModel):
    """Item representing a matched contract chunk with source location."""
    chunk_id: str
    contract_id: str
    contract_name: str
    contract_type: Optional[str] = None
    document_id: str
    file_name: str
    chunk_index: int
    text: str
    page_start: int
    page_end: int
    page_number: int
    section: str = "General"
    source_location: str
    similarity_score: float
    metadata: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class SearchResponseV1(BaseModel):
    """Semantic vector search response."""
    query: str
    result_count: int
    top_k: int
    results: List[SearchResultItemV1]
