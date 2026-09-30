import os
from typing import Tuple

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class FileValidationError(Exception):
    """Exception raised when uploaded file validation fails."""
    pass


def validate_uploaded_file(file_path: str, original_filename: str) -> Tuple[bool, str]:
    """
    Validate extension, file size, and magic byte content.
    Returns (True, format_type) or raises FileValidationError.
    """
    if not os.path.exists(file_path):
        raise FileValidationError(f"File not found at path: {file_path}")

    # 1. Check file size
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise FileValidationError("File is empty (0 bytes).")
    if file_size > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(f"File size ({file_size} bytes) exceeds 25MB limit.")

    # 2. Check extension
    _, ext = os.path.splitext(original_filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(f"Unsupported file extension '{ext}'. Allowed: .pdf, .docx")

    # 3. Magic bytes / header check
    format_type = ext.lstrip(".").upper()
    try:
        with open(file_path, "rb") as f:
            header = f.read(10)
            if ext == ".pdf" and not header.startswith(b"%PDF"):
                raise FileValidationError("Corrupted PDF file (invalid magic header).")
            elif ext == ".docx" and not header.startswith(b"PK"):
                raise FileValidationError("Corrupted DOCX file (invalid zip container header).")
    except Exception as err:
        if isinstance(err, FileValidationError):
            raise err
        raise FileValidationError(f"Failed to inspect file magic header: {err}")

    return True, format_type
