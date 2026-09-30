from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db, get_risk_analyzer, RiskAnalyzer
from backend.app.models.models import Contract, RiskFlag, Clause
from backend.app.api.schemas.risks import RiskItemResponse, RiskAnalysisResponseV1
from backend.app.services.risk_analyzer import LEGAL_SAFETY_DISCLAIMER

router = APIRouter(prefix="/contracts", tags=["Risk Analysis"])


@router.get(
    "/{contract_id}/risks",
    response_model=RiskAnalysisResponseV1,
    status_code=status.HTTP_200_OK,
    summary="Get identified contract risks",
    description="Retrieve identified potential contractual risks, severity levels, grounded evidence quotes, and explicit AI safety review disclaimers.",
    responses={
        200: {"description": "Identified potential risks with safety disclaimer."},
        404: {"description": "Contract not found."}
    }
)
def get_contract_risks(
    contract_id: str,
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    risks = db.query(RiskFlag).filter(RiskFlag.contract_id == contract_id).all()
    risk_items = []
    for r in risks:
        loc = "Contract Document Text"
        if r.clause_id:
            clause = db.query(Clause).filter(Clause.id == r.clause_id).first()
            if clause:
                loc = f"Clause ({clause.clause_type}), Page {clause.page_number}"

        risk_items.append(RiskItemResponse(
            risk_id=r.id,
            id=r.id,
            contract_id=r.contract_id,
            clause_id=r.clause_id,
            risk_type=r.risk_type,
            severity=r.severity,
            confidence=round(r.confidence, 4),
            explanation=r.description,
            description=r.description,
            evidence=r.evidence,
            source_location=loc,
            created_at=r.created_at
        ))

    return RiskAnalysisResponseV1(
        contract_id=contract_id,
        risk_count=len(risk_items),
        disclaimer=LEGAL_SAFETY_DISCLAIMER,
        risks=risk_items
    )


@router.post(
    "/{contract_id}/analyze-risks",
    response_model=RiskAnalysisResponseV1,
    status_code=status.HTTP_200_OK,
    summary="Trigger contract risk analysis pipeline",
    description="Execute hybrid risk detection (unlimited liability, broad indemnification, automatic renewal, restrictive termination, unusual IP provisions) across contract clauses.",
    responses={
        200: {"description": "Detected contract risks with safety disclaimer."},
        404: {"description": "Contract not found."},
        500: {"description": "Risk analysis pipeline error."}
    }
)
def analyze_contract_risks(
    contract_id: str,
    db: Session = Depends(get_db),
    analyzer: RiskAnalyzer = Depends(get_risk_analyzer)
):
    try:
        risks = analyzer.analyze_and_store_contract_risks(db=db, contract_id=contract_id)
        risk_items = []
        for r in risks:
            loc = "Contract Document Text"
            if r.clause_id:
                clause = db.query(Clause).filter(Clause.id == r.clause_id).first()
                if clause:
                    loc = f"Clause ({clause.clause_type}), Page {clause.page_number}"

            risk_items.append(RiskItemResponse(
                risk_id=r.id,
                id=r.id,
                contract_id=r.contract_id,
                clause_id=r.clause_id,
                risk_type=r.risk_type,
                severity=r.severity,
                confidence=round(r.confidence, 4),
                explanation=r.description,
                description=r.description,
                evidence=r.evidence,
                source_location=loc,
                created_at=r.created_at
            ))

        return RiskAnalysisResponseV1(
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
