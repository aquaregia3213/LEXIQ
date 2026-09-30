from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.contract import SearchRequest, SearchResponse, SearchResultItem
from backend.app.services.search import get_search_service, SearchService

router = APIRouter(prefix="/api/search", tags=["Semantic Search"])


@router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
def perform_semantic_search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Perform semantic vector search over contract chunks.
    Filters by optional metadata parameters (contract_id, contract_type, section).
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty."
        )

    results = search_service.semantic_search(
        db=db,
        query=request.query,
        contract_id=request.contract_id,
        contract_type=request.contract_type,
        section=request.section,
        top_k=request.top_k or 5,
        min_score=request.min_score or 0.0
    )

    items = [SearchResultItem(**item) for item in results]

    return SearchResponse(
        query=request.query,
        result_count=len(items),
        top_k=request.top_k or 5,
        results=items
    )
