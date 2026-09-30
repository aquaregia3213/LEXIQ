import re
import uuid
from typing import List, Dict, Any

# Regex patterns for identifying contractual section headers
SECTION_HEADER_PATTERNS = [
    r"^(ARTICLE|SECTION|CLAUSE)\s+[\dIVXLCDM\.]+",
    r"^\d+[\.\)]\s+[A-Z]",
    r"^[A-Z\s]{4,80}$",
    r"^(CONFIDENTIALITY|INDEMNIFICATION|LIMITATION OF LIABILITY|TERMINATION|RENEWAL|GOVERNING LAW|DISPUTE RESOLUTION|WARRANTIES|MISCELLANEOUS)"
]
SECTION_HEADER_REGEX = re.compile("|".join(SECTION_HEADER_PATTERNS), re.IGNORECASE)


def is_section_header(text: str) -> bool:
    """Determine if a single line snippet represents a contract section header."""
    clean_line = text.strip()
    if not clean_line or len(clean_line) > 100:
        return False
    return bool(SECTION_HEADER_REGEX.match(clean_line))


def chunk_document_pages(
    parsed_doc: Dict[str, Any],
    max_chunk_chars: int = 1000,
    overlap_chars: int = 150
) -> List[Dict[str, Any]]:
    """
    Semantic section-aware document chunker.
    Splits document pages into chunks preserving section boundaries,
    page_start, page_end, section references, chunk IDs, and metadata.
    Rejects empty or whitespace-only chunks.
    """
    chunks: List[Dict[str, Any]] = []
    chunk_counter = 1
    pages = parsed_doc.get("pages", [])

    if not pages:
        return chunks

    current_section = "General"
    current_chunk_paragraphs: List[str] = []
    current_chunk_char_count = 0
    chunk_start_page = 1

    for page in pages:
        page_num = page.get("page_number", 1)
        page_text = page.get("text", "")

        if not page_text or not page_text.strip():
            continue

        # Process lines and paragraphs
        raw_blocks = [p.strip() for p in page_text.split("\n") if p.strip()]

        for block in raw_blocks:
            if not block:
                continue

            header_detected = is_section_header(block)

            # Section-aware split: if a section header is detected and we already have accumulated text, finalize preceding chunk
            if header_detected and current_chunk_paragraphs:
                chunk_text = "\n\n".join(current_chunk_paragraphs).strip()
                if chunk_text:  # Reject empty chunks
                    chunks.append(build_chunk_dict(
                        chunk_index=chunk_counter,
                        text=chunk_text,
                        page_start=chunk_start_page,
                        page_end=page_num,
                        section=current_section
                    ))
                    chunk_counter += 1

                current_chunk_paragraphs = []
                current_chunk_char_count = 0
                chunk_start_page = page_num
                current_section = block
            elif header_detected:
                current_section = block

            block_len = len(block)

            # Max char limit split
            if current_chunk_char_count + block_len > max_chunk_chars and current_chunk_paragraphs:
                chunk_text = "\n\n".join(current_chunk_paragraphs).strip()
                if chunk_text:  # Reject empty chunks
                    chunks.append(build_chunk_dict(
                        chunk_index=chunk_counter,
                        text=chunk_text,
                        page_start=chunk_start_page,
                        page_end=page_num,
                        section=current_section
                    ))
                    chunk_counter += 1

                overlap_text = chunk_text[-overlap_chars:] if len(chunk_text) > overlap_chars else ""
                current_chunk_paragraphs = [overlap_text, block] if overlap_text else [block]
                current_chunk_char_count = sum(len(p) for p in current_chunk_paragraphs)
                chunk_start_page = page_num
            else:
                if not current_chunk_paragraphs:
                    chunk_start_page = page_num
                current_chunk_paragraphs.append(block)
                current_chunk_char_count += block_len

    # Finalize trailing chunk
    if current_chunk_paragraphs:
        final_text = "\n\n".join(current_chunk_paragraphs).strip()
        if final_text:  # Reject empty chunks
            last_page = pages[-1].get("page_number", chunk_start_page) if pages else chunk_start_page
            chunks.append(build_chunk_dict(
                chunk_index=chunk_counter,
                text=final_text,
                page_start=chunk_start_page,
                page_end=last_page,
                section=current_section
            ))

    return chunks


def build_chunk_dict(
    chunk_index: int,
    text: str,
    page_start: int,
    page_end: int,
    section: str
) -> Dict[str, Any]:
    """Helper constructing validated chunk dictionary with complete metadata."""
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Cannot build chunk dictionary for empty text.")

    words = clean_text.split()
    chunk_id = str(uuid.uuid4())

    metadata = {
        "chunk_id": chunk_id,
        "chunk_index": chunk_index,
        "section": section,
        "page_start": page_start,
        "page_end": page_end,
        "char_count": len(clean_text),
        "word_count": len(words),
        "has_section_header": section != "General"
    }

    return {
        "chunk_id": chunk_id,
        "chunk_index": chunk_index,
        "text": clean_text,
        "page_start": page_start,
        "page_end": page_end,
        "section": section,
        "char_count": len(clean_text),
        "word_count": len(words),
        "metadata": metadata
    }
