from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field


class ContractUploadResponse(BaseModel):
    """Response schema returned following successful document upload."""
    contract_id: str
    filename: str
    processing_status: str
    document_id: Optional[str] = None
    contract_name: Optional[str] = None
    file_type: Optional[str] = None
    page_count: Optional[int] = 0
    chunk_count: Optional[int] = 0
    message: Optional[str] = "Contract uploaded and processed successfully."

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ContractStatusResponse(BaseModel):
    """Document processing and lifecycle status response."""
    contract_id: str
    name: str
    contract_type: Optional[str] = None
    status: str
    processing_status: str
    page_count: int = 0
    chunk_count: int = 0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ContractSummaryResponse(BaseModel):
    """Summary item for contracts listing."""
    id: str
    name: str
    contract_type: Optional[str] = None
    status: str
    file_path: Optional[str] = None
    uploaded_by: Optional[str] = None
    page_count: Optional[int] = 0
    chunk_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChunkDetailResponse(BaseModel):
    """Processed document chunk item with source metadata."""
    chunk_id: str
    id: str
    contract_id: str
    document_id: str
    chunk_index: int
    text: str
    page_start: int
    page_end: int
    section: str = "General"
    source_location: str
    metadata: Optional[Any] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
