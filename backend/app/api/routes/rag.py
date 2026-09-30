from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db, get_rag_pipeline, RAGPipeline
from backend.app.api.schemas.rag import RAGQueryRequestV1, RAGQueryResponseV1, RAGSourceCitationV1

router = APIRouter(prefix="/rag", tags=["RAG Question Answering"])


@router.post(
    "/query",
    response_model=RAGQueryResponseV1,
    status_code=status.HTTP_200_OK,
    summary="Ask question over contracts (RAG)",
    description="Perform grounded Retrieval-Augmented Generation question-answering over contract documents with source citations and evidence sufficiency indicators.",
    responses={
        200: {"description": "Synthesized grounded answer with source citations."},
        400: {"description": "Question parameter cannot be empty."}
    }
)
def query_contracts_rag(
    request: RAGQueryRequestV1,
    db: Session = Depends(get_db),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question parameter cannot be empty."
        )

    result = rag_pipeline.ask_question(
        db=db,
        question=request.question.strip(),
        contract_id=request.contract_id,
        top_k=request.top_k or 5
    )

    sources = []
    for src in result.get("sources", []):
        p_start = src.get("page_start", 1)
        p_end = src.get("page_end", 1)
        sec = src.get("section", "General")
        loc = f"Page {p_start}" if p_start == p_end else f"Pages {p_start}-{p_end}"
        if sec and sec != "General":
            loc += f", Section: {sec}"

        sources.append(RAGSourceCitationV1(
            chunk_id=src.get("chunk_id"),
            contract_id=src.get("contract_id"),
            contract_name=src.get("contract_name"),
            file_name=src.get("file_name"),
            page_start=p_start,
            page_end=p_end,
            page_number=p_start,
            section=sec,
            source_location=loc,
            text=src.get("text")
        ))

    return RAGQueryResponseV1(
        question=result["question"],
        answer=result["answer"],
        sources=sources,
        has_sufficient_evidence=result.get("has_sufficient_evidence", True),
        confidence_notes=result.get("confidence_notes")
    )
