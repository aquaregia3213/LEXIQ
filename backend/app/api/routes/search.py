from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db, get_search_service, SearchService
from backend.app.api.schemas.search import SearchRequestV1, SearchResponseV1, SearchResultItemV1

router = APIRouter(prefix="/search", tags=["Semantic Search"])


@router.post(
    "",
    response_model=SearchResponseV1,
    status_code=status.HTTP_200_OK,
    summary="Semantic vector search",
    description="Perform semantic similarity search over contract document chunks using dense embeddings and metadata filtering.",
    responses={
        200: {"description": "Matching contract chunks with similarity scores and page references."},
        400: {"description": "Query parameter cannot be empty."}
    }
)
def perform_semantic_search(
    request: SearchRequestV1,
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service)
):
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty."
        )

    # Extract filters if provided in dictionary
    contract_type = request.contract_type
    section = request.section
    contract_id = request.contract_id

    if request.filters and isinstance(request.filters, dict):
        if not contract_type and "contract_type" in request.filters:
            contract_type = request.filters.get("contract_type")
        if not section and "section" in request.filters:
            section = request.filters.get("section")
        if not contract_id and "contract_id" in request.filters:
            contract_id = request.filters.get("contract_id")

    results = search_service.semantic_search(
        db=db,
        query=request.query.strip(),
        contract_id=contract_id,
        contract_type=contract_type,
        section=section,
        top_k=request.top_k or 5,
        min_score=request.min_score or 0.0
    )

    items = []
    for item in results:
        page_start = item.get("page_start", 1)
        page_end = item.get("page_end", 1)
        section_name = item.get("section", "General")
        loc = f"Page {page_start}" if page_start == page_end else f"Pages {page_start}-{page_end}"
        if section_name and section_name != "General":
            loc += f", Section: {section_name}"

        items.append(SearchResultItemV1(
            chunk_id=item["chunk_id"],
            contract_id=item["contract_id"],
            contract_name=item["contract_name"],
            contract_type=item.get("contract_type"),
            document_id=item["document_id"],
            file_name=item["file_name"],
            chunk_index=item["chunk_index"],
            text=item["text"],
            page_start=page_start,
            page_end=page_end,
            page_number=page_start,
            section=section_name,
            source_location=loc,
            similarity_score=item["similarity_score"],
            metadata=item.get("metadata")
        ))

    return SearchResponseV1(
        query=request.query,
        result_count=len(items),
        top_k=request.top_k or 5,
        results=items
    )
