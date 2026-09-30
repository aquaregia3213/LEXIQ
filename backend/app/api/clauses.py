from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.models import Contract, Clause
from backend.app.schemas.contract import ClauseResponse
from backend.app.services.clause_classifier import get_clause_classifier, ClauseClassifier

router = APIRouter(prefix="/api/contracts", tags=["Clause Classification"])


@router.get("/{contract_id}/clauses", response_model=List[ClauseResponse], status_code=status.HTTP_200_OK)
def get_contract_clauses(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve extracted and classified clauses for a contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    clauses = db.query(Clause).filter(Clause.contract_id == contract_id).all()
    return clauses


@router.post("/{contract_id}/extract-clauses", response_model=List[ClauseResponse], status_code=status.HTTP_200_OK)
def extract_contract_clauses_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    classifier: ClauseClassifier = Depends(get_clause_classifier)
):
    """Trigger clause extraction and classification pipeline on contract text."""
    try:
        clauses = classifier.extract_and_store_clauses(db=db, contract_id=contract_id)
        return clauses
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
