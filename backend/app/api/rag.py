from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.contract import AskRequest, AskResponse, SourceCitation
from backend.app.services.rag import get_rag_pipeline, RAGPipeline

router = APIRouter(prefix="/api/ask", tags=["RAG Question Answering"])


@router.post("", response_model=AskResponse, status_code=status.HTTP_200_OK)
def ask_contract_question(
    request: AskRequest,
    db: Session = Depends(get_db),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Perform grounded Retrieval-Augmented Generation question-answering over contract documents.
    Returns synthesized answer, source citations, evidence status, and legal disclaimer notes.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question parameter cannot be empty."
        )

    result = rag_pipeline.ask_question(
        db=db,
        question=request.question,
        contract_id=request.contract_id,
        top_k=request.top_k or 5
    )

    sources = [SourceCitation(**src) for src in result.get("sources", [])]

    return AskResponse(
        question=result["question"],
        answer=result["answer"],
        sources=sources,
        has_sufficient_evidence=result["has_sufficient_evidence"],
        confidence_notes=result.get("confidence_notes")
    )
