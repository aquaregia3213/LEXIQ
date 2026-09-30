from typing import Optional, Any
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Structured error payload for API error responses."""
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standardized API error response envelope."""
    error: ErrorDetail
    detail: Optional[str] = None
