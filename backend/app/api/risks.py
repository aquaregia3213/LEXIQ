from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.models import Contract, RiskFlag
from backend.app.schemas.contract import RiskAnalysisResponse, RiskFlagResponse
from backend.app.services.risk_analyzer import get_risk_analyzer, RiskAnalyzer, LEGAL_SAFETY_DISCLAIMER

router = APIRouter(prefix="/api/contracts", tags=["Risk Analysis"])


@router.get("/{contract_id}/risks", response_model=RiskAnalysisResponse, status_code=status.HTTP_200_OK)
def get_contract_risks(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve risk flags for a contract with explicit legal safety disclaimers."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    risks = db.query(RiskFlag).filter(RiskFlag.contract_id == contract_id).all()
    risk_items = [RiskFlagResponse.model_validate(r) for r in risks]

    return RiskAnalysisResponse(
        contract_id=contract_id,
        risk_count=len(risk_items),
        disclaimer=LEGAL_SAFETY_DISCLAIMER,
        risks=risk_items
    )


@router.post("/{contract_id}/analyze-risks", response_model=RiskAnalysisResponse, status_code=status.HTTP_200_OK)
def analyze_contract_risks_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    analyzer: RiskAnalyzer = Depends(get_risk_analyzer)
):
    """Trigger hybrid risk analysis pipeline across all contract clauses."""
    try:
        risks = analyzer.analyze_and_store_contract_risks(db=db, contract_id=contract_id)
        risk_items = [RiskFlagResponse.model_validate(r) for r in risks]

        return RiskAnalysisResponse(
            contract_id=contract_id,
            risk_count=len(risk_items),
            disclaimer=LEGAL_SAFETY_DISCLAIMER,
            risks=risk_items
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk analysis failed: {str(err)}"
        )
