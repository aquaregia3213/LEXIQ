try:
    import pymupdf as fitz
except ImportError:
    import fitz  # PyMuPDF
from typing import List, Dict, Any
from ingestion.preprocessing.cleaner import clean_extracted_text


class PDFParsingError(Exception):
    """Exception raised when PDF parsing fails."""
    pass


def parse_pdf_document(file_path: str) -> Dict[str, Any]:
    """
    Parse PDF file using PyMuPDF (fitz).
    Returns dict containing page_count, pages list (page_number, text, blocks), and full_text.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as err:
        raise PDFParsingError(f"PyMuPDF failed to open PDF document: {err}")

    try:
        pages_data: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc.load_page(page_idx)
            raw_text = page.get_text("text")
            cleaned = clean_extracted_text(raw_text)

            pages_data.append({
                "page_number": page_num,
                "text": cleaned,
                "char_count": len(cleaned)
            })
            if cleaned:
                full_text_parts.append(cleaned)

        doc.close()

        return {
            "file_type": "PDF",
            "page_count": len(pages_data),
            "pages": pages_data,
            "full_text": "\n\n".join(full_text_parts)
        }
    except Exception as err:
        if 'doc' in locals():
            doc.close()
        raise PDFParsingError(f"Error parsing PDF content: {err}")
