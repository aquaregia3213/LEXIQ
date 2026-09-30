import os
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db, SessionLocal, engine, Base
from backend.app.models.models import Contract, Document, Chunk
from backend.app.schemas.contract import ContractResponse, DocumentResponse, ChunkResponse
from ingestion.pipeline.ingestor import process_contract_ingestion

router = APIRouter(prefix="/api/contracts", tags=["Contracts"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_contract(
    file: UploadFile = File(...),
    contract_name: Optional[str] = Form(None),
    contract_type: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF or DOCX contract document.
    Executes parsing, text extraction, page tracking, and chunking pipeline.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    result = process_contract_ingestion(
        db=db,
        file_bytes=contents,
        original_filename=file.filename,
        contract_name=contract_name,
        contract_type=contract_type
    )

    if result.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "DOCUMENT_PROCESSING_FAILED",
                    "message": result.get("error_message", "Failed to parse document.")
                }
            }
        )

    return result


@router.get("", response_model=List[ContractResponse])
def list_contracts(db: Session = Depends(get_db)):
    """List all ingested contracts."""
    contracts = db.query(Contract).order_by(Contract.created_at.desc()).all()
    return contracts


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract '{contract_id}' not found.")
    return contract


@router.delete("/{contract_id}", status_code=status.HTTP_200_OK)
def delete_contract(contract_id: str, db: Session = Depends(get_db)):
    """Delete contract, purge stored file from disk, and cascade-delete DB records."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract '{contract_id}' not found.")

    # Remove physical file if it exists
    if contract.file_path and os.path.exists(contract.file_path):
        try:
            os.remove(contract.file_path)
        except Exception:
            pass

    # Purge Knowledge Graph nodes and edges for data lifecycle and privacy compliance
    try:
        from backend.app.services.graph import get_graph_service
        get_graph_service().delete_contract_from_graph(contract_id)
    except Exception:
        pass

    db.delete(contract)
    db.commit()

    return {"message": f"Contract '{contract_id}' successfully deleted."}
