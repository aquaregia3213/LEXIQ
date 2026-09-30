from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class ContractBase(BaseModel):
    name: str
    contract_type: Optional[str] = None
    status: Optional[str] = "PROCESSING"


class ContractCreate(ContractBase):
    file_path: Optional[str] = None
    uploaded_by: Optional[str] = None


class ClauseResponse(BaseModel):
    id: str
    contract_id: str
    document_id: Optional[str] = None
    clause_type: str
    text: str
    page_number: int
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntityResponse(BaseModel):
    id: str
    contract_id: str
    entity_type: str
    name: str
    normalized_name: Optional[str] = None
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObligationResponse(BaseModel):
    id: str
    contract_id: str
    description: str
    party: Optional[str] = None
    deadline: Optional[str] = None
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskFlagResponse(BaseModel):
    id: str
    contract_id: str
    clause_id: Optional[str] = None
    risk_type: str
    severity: str
    description: str
    evidence: Optional[str] = None
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChunkResponse(BaseModel):
    id: str
    contract_id: str
    document_id: str
    chunk_index: int
    text: str
    page_start: int
    page_end: int
    metadata_json: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: str
    contract_id: str
    file_name: str
    file_type: str
    page_count: int
    processing_status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContractResponse(ContractBase):
    id: str
    file_path: Optional[str] = None
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    documents: List[DocumentResponse] = []
    clauses: List[ClauseResponse] = []
    entities: List[EntityResponse] = []
    obligations: List[ObligationResponse] = []
    risk_flags: List[RiskFlagResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SearchRequest(BaseModel):
    query: str
    contract_id: Optional[str] = None
    contract_type: Optional[str] = None
    section: Optional[str] = None
    top_k: Optional[int] = 5
    min_score: Optional[float] = 0.0


class SearchResultItem(BaseModel):
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
    section: str
    similarity_score: float
    metadata: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    query: str
    result_count: int
    top_k: int
    results: List[SearchResultItem]


class AskRequest(BaseModel):
    question: str
    contract_id: Optional[str] = None
    top_k: Optional[int] = 5


class SourceCitation(BaseModel):
    chunk_id: Optional[str] = None
    contract_id: Optional[str] = None
    contract_name: Optional[str] = None
    file_name: Optional[str] = None
    page_start: int = 1
    page_end: int = 1
    section: str = "General"
    text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceCitation] = []
    has_sufficient_evidence: bool = True
    confidence_notes: Optional[str] = None


class RiskAnalysisResponse(BaseModel):
    contract_id: str
    risk_count: int
    disclaimer: str
    risks: List[RiskFlagResponse]



