from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db, get_entity_extractor, EntityExtractor
from backend.app.models.models import Contract, Entity
from backend.app.api.schemas.entities import EntityItemResponse

router = APIRouter(prefix="/contracts", tags=["Entity Extraction"])


@router.get(
    "/{contract_id}/entities",
    response_model=List[EntityItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get extracted contract entities",
    description="Retrieve extracted named entities (companies, persons, dates, monetary amounts, jurisdictions) for a contract.",
    responses={
        200: {"description": "List of extracted entities."},
        404: {"description": "Contract not found."}
    }
)
def get_contract_entities(
    contract_id: str,
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    entities = db.query(Entity).filter(Entity.contract_id == contract_id).all()
    results = []
    for ent in entities:
        results.append(EntityItemResponse(
            entity_id=ent.id,
            id=ent.id,
            contract_id=ent.contract_id,
            entity_type=ent.entity_type,
            text=ent.name,
            name=ent.name,
            normalized_value=ent.normalized_name,
            normalized_name=ent.normalized_name,
            confidence=round(ent.confidence, 4),
            source_location="Contract Document Text",
            created_at=ent.created_at
        ))
    return results


@router.post(
    "/{contract_id}/extract-entities",
    response_model=List[EntityItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Trigger entity extraction pipeline",
    description="Execute named entity extraction and canonical normalization across contract chunks and persist Entity records.",
    responses={
        200: {"description": "Extracted named entities."},
        404: {"description": "Contract not found."},
        500: {"description": "Extraction pipeline error."}
    }
)
def extract_contract_entities(
    contract_id: str,
    db: Session = Depends(get_db),
    extractor: EntityExtractor = Depends(get_entity_extractor)
):
    try:
        entities = extractor.extract_and_store_entities(db=db, contract_id=contract_id)
        results = []
        for ent in entities:
            results.append(EntityItemResponse(
                entity_id=ent.id,
                id=ent.id,
                contract_id=ent.contract_id,
                entity_type=ent.entity_type,
                text=ent.name,
                name=ent.name,
                normalized_value=ent.normalized_name,
                normalized_name=ent.normalized_name,
                confidence=round(ent.confidence, 4),
                source_location="Contract Document Text",
                created_at=ent.created_at
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
            detail=f"Entity extraction failed: {str(err)}"
        )
