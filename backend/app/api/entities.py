from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.models import Contract, Entity
from backend.app.schemas.contract import EntityResponse
from backend.app.services.extractor import get_entity_extractor, EntityExtractor

router = APIRouter(prefix="/api/contracts", tags=["Entity Extraction"])


@router.get("/{contract_id}/entities", response_model=List[EntityResponse], status_code=status.HTTP_200_OK)
def get_contract_entities(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve extracted entities for a contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    entities = db.query(Entity).filter(Entity.contract_id == contract_id).all()
    return entities


@router.post("/{contract_id}/extract-entities", response_model=List[EntityResponse], status_code=status.HTTP_200_OK)
def extract_contract_entities_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    extractor: EntityExtractor = Depends(get_entity_extractor)
):
    """Trigger entity extraction pipeline on contract document chunks."""
    try:
        entities = extractor.extract_and_store_entities(db=db, contract_id=contract_id)
        return entities
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
