import os
import uuid
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.models import Contract, Document, Chunk
from ingestion.preprocessing.validator import validate_uploaded_file, FileValidationError
from ingestion.parsers.pdf_parser import parse_pdf_document, PDFParsingError
from ingestion.parsers.docx_parser import parse_docx_document, DOCXParsingError
from ingestion.chunking.chunker import chunk_document_pages
from backend.app.services.embedding import get_embedding_service

from pathlib import Path
from backend.app.config import settings

logger = logging.getLogger(__name__)


def get_upload_dir() -> str:
    """Return configured upload destination directory path (resolving absolute or relative paths)."""
    cfg_dir = settings.UPLOAD_DIR or "uploads/contracts"
    path = Path(cfg_dir)
    if not path.is_absolute():
        project_root = Path(__file__).resolve().parent.parent.parent
        path = project_root / cfg_dir
    return str(path)


def ensure_upload_dir() -> str:
    """Ensure destination upload directory exists and return directory path."""
    dest = get_upload_dir()
    os.makedirs(dest, exist_ok=True)
    return dest


def process_contract_ingestion(
    db: Session,
    file_bytes: bytes,
    original_filename: str,
    contract_name: str = None,
    contract_type: str = None
) -> Dict[str, Any]:
    """
    Execute full ingestion pipeline for an uploaded contract document.
    Saves file, creates DB records, parses PDF/DOCX, chunks text, and updates processing status.
    """
    upload_dir = ensure_upload_dir()

    # 1. Generate unique file path and save raw file
    file_uuid = str(uuid.uuid4())
    _, ext = os.path.splitext(original_filename.lower())
    saved_filename = f"{file_uuid}{ext}"
    saved_file_path = os.path.join(upload_dir, saved_filename)

    with open(saved_file_path, "wb") as f:
        f.write(file_bytes)

    # 2. Create initial DB records
    display_name = contract_name or os.path.splitext(original_filename)[0]
    contract = Contract(
        name=display_name,
        contract_type=contract_type or "General Contract",
        status="PROCESSING",
        file_path=saved_file_path
    )
    db.add(contract)
    db.flush()

    doc_record = Document(
        contract_id=contract.id,
        file_name=original_filename,
        file_type=ext.lstrip(".").upper(),
        page_count=0,
        processing_status="PROCESSING"
    )
    db.add(doc_record)
    db.flush()

    try:
        # 3. File validation
        validate_uploaded_file(saved_file_path, original_filename)

        # 4. Format-specific parsing
        if ext == ".pdf":
            parsed_data = parse_pdf_document(saved_file_path)
        elif ext == ".docx":
            parsed_data = parse_docx_document(saved_file_path)
        else:
            raise FileValidationError(f"Unsupported file format: {ext}")

        doc_record.page_count = parsed_data.get("page_count", 1)
        doc_record.processing_status = "PARSED"
        db.flush()

        # 5. Semantic chunking
        chunks = chunk_document_pages(parsed_data)
        embedding_service = get_embedding_service()

        # 6. Save chunks to database with vector embeddings (batched for high performance)
        chunk_texts = [chk["text"] for chk in chunks]
        batch_size = 20
        all_embeddings = []
        try:
            for i in range(0, len(chunk_texts), batch_size):
                batch_slice = chunk_texts[i:i + batch_size]
                batch_vecs = embedding_service.embed_batch(batch_slice)
                all_embeddings.extend(batch_vecs)
        except Exception as batch_err:
            logger.warning(f"Batch embedding failed ({batch_err}), falling back to individual embedding.")
            all_embeddings = [embedding_service.embed_text(t) for t in chunk_texts]

        db_chunks = []
        for chk, text_vec in zip(chunks, all_embeddings):
            chunk_rec = Chunk(
                id=chk.get("chunk_id", str(uuid.uuid4())),
                contract_id=contract.id,
                document_id=doc_record.id,
                chunk_index=chk["chunk_index"],
                text=chk["text"],
                page_start=chk["page_start"],
                page_end=chk["page_end"],
                metadata_json=chk["metadata"],
                embedding=text_vec
            )
            db_chunks.append(chunk_rec)

        db.add_all(db_chunks)

        # Update final status
        doc_record.processing_status = "COMPLETED"
        contract.status = "COMPLETED"
        db.commit()
        db.refresh(contract)

        logger.info(f"Successfully ingested contract '{contract.name}' ({len(db_chunks)} chunks).")

        return {
            "status": "success",
            "contract_id": contract.id,
            "document_id": doc_record.id,
            "contract_name": contract.name,
            "file_name": doc_record.file_name,
            "file_type": doc_record.file_type,
            "page_count": doc_record.page_count,
            "chunk_count": len(db_chunks),
            "processing_status": "COMPLETED"
        }

    except Exception as err:
        error_msg = str(err)
        logger.error(f"Ingestion failed for file {original_filename}: {error_msg}")

        # Security & hygiene: remove uploaded physical file if ingestion failed
        if os.path.exists(saved_file_path):
            try:
                os.remove(saved_file_path)
            except Exception:
                pass

        try:
            db.rollback()
            # If contract record was created, mark as failed
            contract.status = "FAILED"
            doc_record.processing_status = "FAILED"
            doc_record.error_message = error_msg
            db.add(contract)
            db.add(doc_record)
            db.commit()
        except Exception:
            db.rollback()

        return {
            "status": "failed",
            "contract_id": getattr(contract, "id", None),
            "document_id": getattr(doc_record, "id", None),
            "file_name": original_filename,
            "error_message": error_msg,
            "processing_status": "FAILED"
        }
