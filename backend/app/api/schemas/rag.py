from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class RAGQueryRequestV1(BaseModel):
    """Payload for grounded RAG question-answering."""
    question: str
    contract_id: Optional[str] = None
    top_k: Optional[int] = 5


class RAGSourceCitationV1(BaseModel):
    """Source citation reference for RAG answer evidence grounding."""
    chunk_id: Optional[str] = None
    contract_id: Optional[str] = None
    contract_name: Optional[str] = None
    file_name: Optional[str] = None
    page_start: int = 1
    page_end: int = 1
    page_number: int = 1
    section: str = "General"
    source_location: Optional[str] = None
    text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RAGQueryResponseV1(BaseModel):
    """Synthesized RAG QA response with supporting source citations."""
    question: str
    answer: str
    sources: List[RAGSourceCitationV1] = []
    has_sufficient_evidence: bool = True
    confidence_notes: Optional[str] = None
