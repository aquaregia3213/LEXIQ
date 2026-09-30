import re


def clean_extracted_text(text: str) -> str:
    """
    Clean extracted text by normalizing whitespace while preserving legal text formatting.
    Does not modify wording or numbers.
    """
    if not text:
        return ""

    # Replace null bytes
    cleaned = text.replace("\x00", "")

    # Normalize carriage returns
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # Replace non-breaking spaces with standard space
    cleaned = cleaned.replace("\xa0", " ")

    # Collapse multi-blank spaces within lines while preserving newlines
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    # Collapse excessive blank lines (more than 2 consecutive newlines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()
