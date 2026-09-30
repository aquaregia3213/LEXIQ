# Document Processing

## Objective

Convert uploaded contract files into structured, searchable content.

## Pipeline

```text
Upload
 ↓
Validation
 ↓
File Storage
 ↓
Parser
 ↓
Text Extraction
 ↓
Cleaning
 ↓
Structure Detection
 ↓
Chunking
 ↓
Metadata
 ↓
Embedding
```

## Supported Formats

MVP:

- PDF
- DOCX

Future:

- scanned PDF
- images
- OCR

## File Validation

Validate:

- extension
- MIME type
- file size
- corrupted files

Never trust the filename alone.

## Text Extraction

Preserve:

- text
- page numbers
- headings
- section boundaries where possible

## Cleaning

Remove:

- duplicated headers
- duplicated footers
- irrelevant whitespace
- extraction artifacts

Do not aggressively modify legal text.

The original text must remain recoverable.

## Chunking

Chunks should preserve semantic meaning.

Prefer chunking based on:

- headings
- sections
- paragraphs
- clause boundaries

Avoid blindly splitting every N characters.

## Chunk Metadata

Each chunk should contain:

```json
{
  "contract_id": "...",
  "document_id": "...",
  "chunk_index": 10,
  "page_start": 12,
  "page_end": 13,
  "section": "Termination",
  "text": "..."
}
```

## OCR

OCR should be treated as a separate processing path.

OCR output should be marked as OCR-derived because extraction quality can differ from digitally generated text.

## Processing Status

Use:

```text
UPLOADED
PROCESSING
PARSED
INDEXED
COMPLETED
FAILED
```

## Error Handling

A single corrupted document must not terminate processing of the entire repository.

Record processing errors for debugging.