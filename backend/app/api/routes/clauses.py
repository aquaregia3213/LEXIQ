from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db, get_clause_classifier, ClauseClassifier
from backend.app.models.models import Contract, Clause
from backend.app.api.schemas.clauses import ClauseItemResponse

router = APIRouter(prefix="/contracts", tags=["Clause Classification"])


@router.get(
    "/{contract_id}/clauses",
    response_model=List[ClauseItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get extracted contract clauses",
    description="Retrieve extracted and classified clauses for a contract, including clause taxonomy type, confidence, and page location.",
    responses={
        200: {"description": "List of classified clauses."},
        404: {"description": "Contract not found."}
    }
)
def get_contract_clauses(
    contract_id: str,
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    clauses = db.query(Clause).filter(Clause.contract_id == contract_id).all()
    results = []
    for cl in clauses:
        loc = f"Page {cl.page_number}"
        results.append(ClauseItemResponse(
            clause_id=cl.id,
            id=cl.id,
            contract_id=cl.contract_id,
            document_id=cl.document_id,
            clause_type=cl.clause_type,
            text=cl.text,
            confidence=round(cl.confidence, 4),
            page_number=cl.page_number,
            source_location=loc,
            created_at=cl.created_at
        ))
    return results


@router.post(
    "/{contract_id}/extract-clauses",
    response_model=List[ClauseItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Trigger clause extraction pipeline",
    description="Execute clause detection and classification pipeline across all contract chunks and persist Clause records.",
    responses={
        200: {"description": "Extracted and classified clauses."},
        404: {"description": "Contract not found."},
        500: {"description": "Extraction pipeline error."}
    }
)
def extract_contract_clauses(
    contract_id: str,
    db: Session = Depends(get_db),
    classifier: ClauseClassifier = Depends(get_clause_classifier)
):
    try:
        clauses = classifier.extract_and_store_clauses(db=db, contract_id=contract_id)
        results = []
        for cl in clauses:
            loc = f"Page {cl.page_number}"
            results.append(ClauseItemResponse(
                clause_id=cl.id,
                id=cl.id,
                contract_id=cl.contract_id,
                document_id=cl.document_id,
                clause_type=cl.clause_type,
                text=cl.text,
                confidence=round(cl.confidence, 4),
                page_number=cl.page_number,
                source_location=loc,
                created_at=cl.created_at
            ))
        return results
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clause extraction failed: {str(err)}"
        )
