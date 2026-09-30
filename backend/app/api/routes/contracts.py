import os
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from backend.app.api.dependencies import get_db
from backend.app.services.graph import get_graph_service
from backend.app.models.models import Contract, Document, Chunk
from backend.app.api.schemas.contracts import (
    ContractUploadResponse,
    ContractStatusResponse,
    ContractSummaryResponse,
    ChunkDetailResponse
)
from backend.app.schemas.contract import ContractResponse
from ingestion.pipeline.ingestor import process_contract_ingestion

router = APIRouter(prefix="/contracts", tags=["Contracts"])


@router.post(
    "/upload",
    response_model=ContractUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a contract document",
    description="Upload a PDF or DOCX contract document. Executes text extraction, page tracking, chunking, and embedding generation.",
    responses={
        201: {"description": "Contract uploaded and processed successfully."},
        400: {"description": "Invalid file format or empty file."},
        422: {"description": "Document parsing or processing failed."}
    }
)
async def upload_contract(
    file: UploadFile = File(..., description="PDF or DOCX contract document"),
    contract_name: Optional[str] = Form(None, description="Optional custom name for the contract"),
    contract_type: Optional[str] = Form(None, description="Optional contract category (e.g., NDA, MSA, Employment)"),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided."
        )

    _, ext = os.path.splitext(file.filename.lower())
    if ext not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: .pdf, .docx"
        )

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

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
            detail=result.get("error_message", "Failed to parse and process document.")
        )

    return ContractUploadResponse(
        contract_id=result["contract_id"],
        filename=result.get("file_name", file.filename),
        processing_status=result.get("processing_status", "COMPLETED"),
        document_id=result.get("document_id"),
        contract_name=result.get("contract_name"),
        file_type=result.get("file_type"),
        page_count=result.get("page_count", 0),
        chunk_count=result.get("chunk_count", 0),
        message="Contract uploaded and processed successfully."
    )


@router.get(
    "",
    response_model=List[ContractSummaryResponse],
    summary="List all contracts",
    description="Retrieve all registered contracts in reverse chronological order.",
    responses={
        200: {"description": "List of contracts."}
    }
)
def list_contracts(db: Session = Depends(get_db)):
    contracts = (
        db.query(Contract)
        .options(selectinload(Contract.documents), selectinload(Contract.chunks))
        .order_by(Contract.created_at.desc())
        .all()
    )
    summary_list = []
    for c in contracts:
        pages = sum(d.page_count or 0 for d in c.documents)
        chunks = len(c.chunks)
        summary_list.append(ContractSummaryResponse(
            id=c.id,
            name=c.name,
            contract_type=c.contract_type,
            status=c.status,
            file_path=c.file_path,
            uploaded_by=c.uploaded_by,
            page_count=pages,
            chunk_count=chunks,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))
    return summary_list


@router.get(
    "/{contract_id}",
    response_model=ContractResponse,
    summary="Get contract details",
    description="Retrieve detailed metadata and relations (clauses, entities, obligations, risks) for a specific contract.",
    responses={
        200: {"description": "Contract details."},
        404: {"description": "Contract not found."}
    }
)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )
    return contract


@router.get(
    "/{contract_id}/status",
    response_model=ContractStatusResponse,
    summary="Get contract processing status",
    description="Retrieve ingestion and processing status for a specific contract.",
    responses={
        200: {"description": "Document processing status."},
        404: {"description": "Contract not found."}
    }
)
def get_contract_status(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    doc = db.query(Document).filter(Document.contract_id == contract_id).first()
    chunks_count = db.query(Chunk).filter(Chunk.contract_id == contract_id).count()

    return ContractStatusResponse(
        contract_id=contract.id,
        name=contract.name,
        contract_type=contract.contract_type,
        status=contract.status,
        processing_status=doc.processing_status if doc else contract.status,
        page_count=doc.page_count if doc else 0,
        chunk_count=chunks_count,
        error_message=doc.error_message if doc else None,
        created_at=contract.created_at,
        updated_at=contract.updated_at
    )


@router.get(
    "/{contract_id}/chunks",
    response_model=List[ChunkDetailResponse],
    summary="Get contract document chunks",
    description="Retrieve all processed document chunks for a contract with exact page references and section metadata.",
    responses={
        200: {"description": "List of document chunks."},
        404: {"description": "Contract not found."}
    }
)
def get_contract_chunks(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    chunks = db.query(Chunk).filter(Chunk.contract_id == contract_id).order_by(Chunk.chunk_index.asc()).all()
    results = []
    for chk in chunks:
        section = "General"
        if chk.metadata_json and isinstance(chk.metadata_json, dict):
            section = chk.metadata_json.get("section", "General")

        loc = f"Page {chk.page_start}" if chk.page_start == chk.page_end else f"Pages {chk.page_start}-{chk.page_end}"
        if section and section != "General":
            loc += f", Section: {section}"

        results.append(ChunkDetailResponse(
            chunk_id=chk.id,
            id=chk.id,
            contract_id=chk.contract_id,
            document_id=chk.document_id,
            chunk_index=chk.chunk_index,
            text=chk.text,
            page_start=chk.page_start,
            page_end=chk.page_end,
            section=section,
            source_location=loc,
            metadata=chk.metadata_json,
            created_at=chk.created_at
        ))
    return results


@router.delete(
    "/{contract_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a contract",
    description="Delete contract metadata, purge physical file from disk, and cascade delete all associated chunks, clauses, entities, obligations, and risk flags.",
    responses={
        200: {"description": "Contract deleted successfully."},
        404: {"description": "Contract not found."}
    }
)
def delete_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    if contract.file_path and os.path.exists(contract.file_path):
        try:
            os.remove(contract.file_path)
        except Exception:
            pass

    # Purge Knowledge Graph nodes and edges for data lifecycle and privacy compliance
    try:
        get_graph_service().delete_contract_from_graph(contract_id)
    except Exception:
        pass

    db.delete(contract)
    db.commit()

    return {"message": f"Contract '{contract_id}' successfully deleted."}
