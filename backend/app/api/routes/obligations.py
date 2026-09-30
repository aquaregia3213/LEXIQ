from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db, get_obligation_extractor, ObligationExtractor
from backend.app.models.models import Contract, Obligation
from backend.app.api.schemas.obligations import ObligationItemResponse

router = APIRouter(prefix="/contracts", tags=["Obligations"])


@router.get(
    "/{contract_id}/obligations",
    response_model=List[ObligationItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get extracted contract obligations",
    description="Retrieve extracted contractual commitments, responsible parties, deadlines, and confidence scores for a contract.",
    responses={
        200: {"description": "List of contractual obligations."},
        404: {"description": "Contract not found."}
    }
)
def get_contract_obligations(
    contract_id: str,
    db: Session = Depends(get_db),
    extractor: ObligationExtractor = Depends(get_obligation_extractor)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    obligations = db.query(Obligation).filter(Obligation.contract_id == contract_id).all()
    if not obligations:
        # On-demand extraction if not previously run
        try:
            obligations = extractor.extract_and_store_obligations(db=db, contract_id=contract_id)
        except Exception:
            obligations = []

    results = []
    for ob in obligations:
        results.append(ObligationItemResponse(
            obligation_id=ob.id,
            id=ob.id,
            contract_id=ob.contract_id,
            obligation=ob.description,
            description=ob.description,
            responsible_party=ob.party,
            party=ob.party,
            deadline=ob.deadline,
            confidence=round(ob.confidence, 4),
            source_location="Contract Document Text",
            created_at=ob.created_at
        ))
    return results


@router.post(
    "/{contract_id}/extract-obligations",
    response_model=List[ObligationItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Trigger obligation extraction pipeline",
    description="Execute obligation detection across contract clauses and document chunks, identifying responsible parties, temporal constraints, and storing Obligation records.",
    responses={
        200: {"description": "Extracted contractual obligations."},
        404: {"description": "Contract not found."},
        500: {"description": "Extraction pipeline error."}
    }
)
def extract_contract_obligations(
    contract_id: str,
    db: Session = Depends(get_db),
    extractor: ObligationExtractor = Depends(get_obligation_extractor)
):
    try:
        obligations = extractor.extract_and_store_obligations(db=db, contract_id=contract_id)
        results = []
        for ob in obligations:
            results.append(ObligationItemResponse(
                obligation_id=ob.id,
                id=ob.id,
                contract_id=ob.contract_id,
                obligation=ob.description,
                description=ob.description,
                responsible_party=ob.party,
                party=ob.party,
                deadline=ob.deadline,
                confidence=round(ob.confidence, 4),
                source_location="Contract Document Text",
                created_at=ob.created_at
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
            detail=f"Obligation extraction failed: {str(err)}"
        )
