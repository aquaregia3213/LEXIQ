# Legal AI Contract Intelligence Platform — REST API Contract (v1)

This specification defines the complete HTTP REST API interface exposed by the backend for frontend developers. The frontend can be built entirely against this document without reading backend Python source code.

---

## 1. Global Specifications

### Base URL
* **Development Server**: `http://localhost:8000/api/v1`
* **Root URL**: `http://localhost:8000`
* **Interactive Swagger UI**: `http://localhost:8000/docs`
* **Interactive ReDoc UI**: `http://localhost:8000/redoc`
* **OpenAPI Specification**: `http://localhost:8000/openapi.json`

### Content Types
* All JSON endpoints accept and return `application/json`.
* Document upload endpoint accepts `multipart/form-data`.

### Standard Error Response Envelope
Every HTTP error status (400, 404, 422, 500) returns a consistent JSON envelope containing both `error` and `detail`:

```json
{
  "detail": "Descriptive human-readable error summary",
  "error": {
    "code": "NOT_FOUND",
    "message": "Contract with id 'd3b07384-d113-4a11-b94f-4d334582f0c1' not found.",
    "details": null
  }
}
```

Standard Error Codes:
* `BAD_REQUEST` (400): Missing required parameters, invalid format, empty query.
* `NOT_FOUND` (404): Resource not found.
* `VALIDATION_ERROR` (422): Schema validation failure.
* `INTERNAL_SERVER_ERROR` (500): Server-side unexpected failure.

---

## 2. Endpoints Reference

---

### CONTRACTS

#### 1. Upload Contract Document
* **METHOD**: `POST`
* **PATH**: `/api/v1/contracts/upload`
* **PURPOSE**: Upload a PDF or DOCX contract document. Triggers parsing, text extraction, semantic chunking, and dense vector embedding generation.
* **REQUEST**:
  * **Content-Type**: `multipart/form-data`
  * **Form Fields**:
    * `file` (File, Required): Binary PDF or DOCX file.
    * `contract_name` (string, Optional): Human-readable contract title (defaults to filename).
    * `contract_type` (string, Optional): Category, e.g., `"Non-Disclosure Agreement"`, `"Master Services Agreement"`.
* **RESPONSE**:
  * **Status**: `201 Created`
  * **Schema**:
    ```json
    {
      "contract_id": "string (UUID)",
      "filename": "string",
      "processing_status": "COMPLETED",
      "document_id": "string (UUID)",
      "contract_name": "string",
      "file_type": "PDF",
      "page_count": 5,
      "chunk_count": 12,
      "message": "Contract uploaded and processed successfully."
    }
    ```
* **ERRORS**:
  * `400 Bad Request`: Empty file or unsupported file extension.
  * `422 Unprocessable Content`: Corrupted file or parsing failure.
* **EXAMPLE REQUEST**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/contracts/upload" \
    -F "file=@nda_agreement.pdf" \
    -F "contract_name=Mutual NDA - Acme Corp" \
    -F "contract_type=Non-Disclosure Agreement"
  ```
* **EXAMPLE RESPONSE**:
  ```json
  {
    "contract_id": "8f03c05c-efbc-4ea1-b27b-58679d67a14e",
    "filename": "nda_agreement.pdf",
    "processing_status": "COMPLETED",
    "document_id": "b3e34b9d-aef2-48a7-96a9-85885c3f6f1c",
    "contract_name": "Mutual NDA - Acme Corp",
    "file_type": "PDF",
    "page_count": 3,
    "chunk_count": 7,
    "message": "Contract uploaded and processed successfully."
  }
  ```

---

#### 2. List All Contracts
* **METHOD**: `GET`
* **PATH**: `/api/v1/contracts`
* **PURPOSE**: Retrieve the list of all ingested contracts in reverse chronological order.
* **REQUEST**: None.
* **RESPONSE**:
  * **Status**: `200 OK`
  * **Schema**: Array of Contract summaries.
* **ERRORS**: None.
* **EXAMPLE REQUEST**:
  ```bash
  curl -X GET "http://localhost:8000/api/v1/contracts"
  ```
* **EXAMPLE RESPONSE**:
  ```json
  [
    {
      "id": "8f03c05c-efbc-4ea1-b27b-58679d67a14e",
      "name": "Mutual NDA - Acme Corp",
      "contract_type": "Non-Disclosure Agreement",
      "status": "COMPLETED",
      "file_path": "/uploads/contracts/8f03c05c.pdf",
      "uploaded_by": null,
      "page_count": 3,
      "chunk_count": 7,
      "created_at": "2026-09-06T06:20:00.000Z",
      "updated_at": "2026-09-06T06:20:05.000Z"
    }
  ]
  ```

---

#### 3. Get Contract Details
* **METHOD**: `GET`
* **PATH**: `/api/v1/contracts/{contract_id}`
* **PURPOSE**: Retrieve contract metadata and all associated nested relational records (documents, clauses, entities, obligations, risk flags).
* **REQUEST**:
  * **Path Parameters**: `contract_id` (string, Required)
* **RESPONSE**:
  * **Status**: `200 OK`
  * **Schema**: Full contract object with nested child arrays.
* **ERRORS**:
  * `404 Not Found`: Contract not found.
* **EXAMPLE REQUEST**:
  ```bash
  curl -X GET "http://localhost:8000/api/v1/contracts/8f03c05c-efbc-4ea1-b27b-58679d67a14e"
  ```
* **EXAMPLE RESPONSE**:
  ```json
  {
    "id": "8f03c05c-efbc-4ea1-b27b-58679d67a14e",
    "name": "Mutual NDA - Acme Corp",
    "contract_type": "Non-Disclosure Agreement",
    "status": "COMPLETED",
    "file_path": "/uploads/contracts/8f03c05c.pdf",
    "uploaded_by": null,
    "created_at": "2026-09-06T06:20:00.000Z",
    "updated_at": "2026-09-06T06:20:05.000Z",
    "documents": [
      {
        "id": "b3e34b9d-aef2-48a7-96a9-85885c3f6f1c",
        "contract_id": "8f03c05c-efbc-4ea1-b27b-58679d67a14e",
        "file_name": "nda_agreement.pdf",
        "file_type": "PDF",
        "page_count": 3,
        "processing_status": "COMPLETED",
        "error_message": null,
        "created_at": "2026-09-06T06:20:00.000Z"
      }
    ],
    "clauses": [],
    "entities": [],
    "obligations": [],
    "risk_flags": []
  }
  ```

---

#### 4. Get Contract Processing Status
* **METHOD**: `GET`
* **PATH**: `/api/v1/contracts/{contract_id}/status`
* **PURPOSE**: Lightweight polling endpoint to check document ingestion progress.
* **REQUEST**:
  * **Path Parameters**: `contract_id` (string, Required)
* **RESPONSE**:
  * **Status**: `200 OK`
* **ERRORS**:
  * `404 Not Found`: Contract not found.
* **EXAMPLE REQUEST**:
  ```bash
  curl -X GET "http://localhost:8000/api/v1/contracts/8f03c05c-efbc-4ea1-b27b-58679d67a14e/status"
  ```
* **EXAMPLE RESPONSE**:
  ```json
  {
    "contract_id": "8f03c05c-efbc-4ea1-b27b-58679d67a14e",
    "name": "Mutual NDA - Acme Corp",
    "contract_type": "Non-Disclosure Agreement",
    "status": "COMPLETED",
    "processing_status": "COMPLETED",
    "page_count": 3,
    "chunk_count": 7,
    "error_message": null,
    "created_at": "2026-09-06T06:20:00.000Z",
    "updated_at": "2026-09-06T06:20:05.000Z"
  }
  ```

---

#### 5. Get Document Chunks
* **METHOD**: `GET`
* **PATH**: `/api/v1/contracts/{contract_id}/chunks`
* **PURPOSE**: Retrieve all semantic document chunks for a contract, including exact page ranges, section headings, and text.
* **REQUEST**:
  * **Path Parameters**: `contract_id` (string, Required)
* **RESPONSE**:
  * **Status**: `200 OK`
* **ERRORS**:
  * `404 Not Found`: Contract not found.
* **EXAMPLE REQUEST**:
  ```bash
  curl -X GET "http://localhost:8000/api/v1/contracts/8f03c05c-efbc-4ea1-b27b-58679d67a14e/chunks"
  ```
* **EXAMPLE RESPONSE**:
  ```json
  [
    {
      "chunk_id": "7585579f-6824-4f01-9b0d-b45a49c95dfc",
      "id": "7585579f-6824-4f01-9b0d-b45a49c95dfc",
      "contract_id": "8f03c05c-efbc-4ea1-b27b-58679d67a14e",
      "document_id": "b3e34b9d-aef2-48a7-96a9-85885c3f6f1c",
      "chunk_index": 0,
      "text": "Section 1: Confidential Information. Receiving Party agrees to prevent unauthorized disclosure...",
      "page_start": 1,
      "page_end": 1,
      "section": "Confidentiality",
      "source_location": "Page 1, Section: Confidentiality",
      "metadata": {
        "section": "Confidentiality",
        "char_count": 210
      },
      "created_at": "2026-09-06T06:20:02.000Z"
    }
  ]
  ```

---

#### 6. Delete Contract
* **METHOD**: `DELETE`
* **PATH**: `/api/v1/contracts/{contract_id}`
* **PURPOSE**: Delete contract record, stored binary file from disk, and cascade-delete all chunks, clauses, entities, obligations, and risk flags.
* **REQUEST**:
  * **Path Parameters**: `contract_id` (string, Required)
* **RESPONSE**:
  * **Status**: `200 OK`
* **EXAMPLE RESPONSE**:
  ```json
  {
    "message": "Contract '8f03c05c-efbc-4ea1-b27b-58679d67a14e' successfully deleted."
  }
  ```

---

### SEMANTIC SEARCH

#### 7. Semantic Vector Search
* **METHOD**: `POST`
* **PATH**: `/api/v1/search`
* **PURPOSE**: Natural language search over contract chunks using vector embeddings and optional metadata filters.
* **REQUEST**:
  * **Body Schema**:
    ```json
    {
      "query": "contracts with automatic renewal provisions",
      "contract_id": "optional-uuid",
      "filters": {
        "contract_type": "NDA",
        "section": "Renewal"
      },
      "top_k": 5,
      "min_score": 0.0
    }
    ```
* **RESPONSE**:
  * **Status**: `200 OK`
  * **Schema**:
    ```json
    {
      "query": "string",
      "result_count": 1,
      "top_k": 5,
      "results": [
        {
          "chunk_id": "string",
          "contract_id": "string",
          "contract_name": "string",
          "contract_type": "string",
          "document_id": "string",
          "file_name": "string",
          "chunk_index": 1,
          "text": "string",
          "page_start": 2,
          "page_end": 2,
          "page_number": 2,
          "section": "Term and Renewal",
          "source_location": "Page 2, Section: Term and Renewal",
          "similarity_score": 0.8842,
          "metadata": {}
        }
      ]
    }
    ```
* **ERRORS**:
  * `400 Bad Request`: Query is empty.
* **EXAMPLE REQUEST**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "confidentiality duration", "top_k": 3}'
  ```

---

### RAG QUESTION ANSWERING

#### 8. RAG Query
* **METHOD**: `POST`
* **PATH**: `/api/v1/rag/query`
* **PURPOSE**: Grounded question-answering over contract documents. Returns synthesized answer with verified source citations. Clearly indicates if evidence is insufficient.
* **REQUEST**:
  * **Body Schema**:
    ```json
    {
      "question": "What is the notice period for terminating the agreement?",
      "contract_id": "optional-uuid",
      "top_k": 5
    }
    ```
* **RESPONSE**:
  * **Status**: `200 OK`
  * **Schema**:
    ```json
    {
      "question": "string",
      "answer": "string",
      "sources": [
        {
          "chunk_id": "string",
          "contract_id": "string",
          "contract_name": "string",
          "file_name": "string",
          "page_start": 2,
          "page_end": 2,
          "page_number": 2,
          "section": "Termination",
          "source_location": "Page 2, Section: Termination"
        }
      ],
      "has_sufficient_evidence": true,
      "confidence_notes": "Grounding verification: 1 supporting sources identified."
    }
    ```
* **INSUFFICIENT EVIDENCE RESPONSE EXAMPLE**:
  When documents do not contain evidence:
  ```json
  {
    "question": "What is the penalty fee?",
    "answer": "The available documents do not provide sufficient evidence to answer this question.",
    "sources": [],
    "has_sufficient_evidence": false,
    "confidence_notes": "No relevant contract documents were found matching your search query."
  }
  ```

---

### CLAUSES

#### 9. Get Contract Clauses
* **METHOD**: `GET`
* **PATH**: `/api/v1/contracts/{contract_id}/clauses`
* **PURPOSE**: Retrieve extracted and classified contract clauses with taxonomy categories and confidence scores.
* **REQUEST**:
  * **Path Parameters**: `contract_id` (string, Required)
* **RESPONSE**:
  * **Status**: `200 OK`
  * **Schema**:
    ```json
    [
      {
        "clause_id": "string",
        "id": "string",
        "contract_id": "string",
        "document_id": "string",
        "clause_type": "Termination",
        "text": "Either party may terminate upon 30 days written notice.",
        "confidence": 0.92,
        "page_number": 2,
        "source_location": "Page 2",
        "created_at": "2026-09-06T06:20:00.000Z"
      }
    ]
    ```

#### 10. Trigger Clause Extraction
* **METHOD**: `POST`
* **PATH**: `/api/v1/contracts/{contract_id}/extract-clauses`
* **PURPOSE**: Run or re-run clause extraction and classification pipeline on contract text.

---

### ENTITIES

#### 11. Get Contract Entities
* **METHOD**: `GET`
* **PATH**: `/api/v1/contracts/{contract_id}/entities`
* **PURPOSE**: Retrieve extracted named entities (companies, persons, jurisdictions, dates, monetary amounts).
* **REQUEST**:
  * **Path Parameters**: `contract_id` (string, Required)
* **RESPONSE**:
  * **Status**: `200 OK`
  * **Schema**:
    ```json
    [
      {
        "entity_id": "string",
        "id": "string",
        "contract_id": "string",
        "entity_type": "COMPANY",
        "text": "Acme Inc.",
        "name": "Acme Inc.",
        "normalized_value": "Acme Incorporated",
        "normalized_name": "Acme Incorporated",
        "confidence": 0.95,
        "source_location": "Contract Document Text",
        "created_at": "2026-09-06T06:20:00.000Z"
      }
    ]
    ```

#### 12. Trigger Entity Extraction
* **METHOD**: `POST`
* **PATH**: `/api/v1/contracts/{contract_id}/extract-entities`
* **PURPOSE**: Run or re-run entity extraction pipeline.

---

### OBLIGATIONS

#### 13. Get Contract Obligations
* **METHOD**: `GET`
* **PATH**: `/api/v1/contracts/{contract_id}/obligations`
* **PURPOSE**: Retrieve contractual obligations, responsible parties, and deadlines.
* **REQUEST**:
  * **Path Parameters**: `contract_id` (string, Required)
* **RESPONSE**:
  * **Status**: `200 OK`
  * **Schema**:
    ```json
    [
      {
        "obligation_id": "string",
        "id": "string",
        "contract_id": "string",
        "obligation": "Deliver quarterly compliance reports within 30 days of quarter end",
        "description": "Deliver quarterly compliance reports within 30 days of quarter end",
        "responsible_party": "Acme Inc.",
        "party": "Acme Inc.",
        "deadline": "within 30 days of quarter end",
        "confidence": 0.88,
        "source_location": "Contract Document Text",
        "created_at": "2026-09-06T06:20:00.000Z"
      }
    ]
    ```

#### 14. Trigger Obligation Extraction
* **METHOD**: `POST`
* **PATH**: `/api/v1/contracts/{contract_id}/extract-obligations`
* **PURPOSE**: Run or re-run obligation extraction pipeline.

---

### RISK ANALYSIS

#### 15. Get Contract Risks
* **METHOD**: `GET`
* **PATH**: `/api/v1/contracts/{contract_id}/risks`
* **PURPOSE**: Retrieve identified potential contract risk flags with severity levels, evidence snippets, and explicit human-review legal disclaimer.
* **REQUEST**:
  * **Path Parameters**: `contract_id` (string, Required)
* **RESPONSE**:
  * **Status**: `200 OK`
  * **Schema**:
    ```json
    {
      "contract_id": "string",
      "risk_count": 1,
      "disclaimer": "This is an AI-generated potential risk flag for human review only. It does not constitute formal legal advice, legal opinion, or legal certainty.",
      "risks": [
        {
          "risk_id": "string",
          "id": "string",
          "contract_id": "string",
          "clause_id": "string",
          "risk_type": "automatic_renewal",
          "severity": "MEDIUM",
          "confidence": 0.88,
          "explanation": "Potential risk detected: Clause provides for automatic term renewal unless explicit cancellation notice is served.",
          "description": "Potential risk detected: Clause provides for automatic term renewal unless explicit cancellation notice is served.",
          "evidence": "automatically renew",
          "source_location": "Clause (Renewal), Page 2",
          "created_at": "2026-09-06T06:20:00.000Z"
        }
      ]
    }
    ```

#### 16. Trigger Risk Analysis
* **METHOD**: `POST`
* **PATH**: `/api/v1/contracts/{contract_id}/analyze-risks`
* **PURPOSE**: Run or re-run risk analysis pipeline across clauses.

---

### KNOWLEDGE GRAPH

#### 17. Get Contract Graph Subgraph
* **METHOD**: `GET`
* **PATH**: `/api/v1/contracts/{contract_id}/graph`
* **PURPOSE**: Retrieve nodes and directed relationship edges formatted for UI graph visualizers (e.g., Cytoscape.js, vis-network, React Flow).
* **REQUEST**:
  * **Path Parameters**: `contract_id` (string, Required)
* **RESPONSE**:
  * **Status**: `200 OK`
  * **Schema**:
    ```json
    {
      "contract_id": "8f03c05c-efbc-4ea1-b27b-58679d67a14e",
      "node_count": 5,
      "relationship_count": 4,
      "nodes": [
        {
          "id": "8f03c05c-efbc-4ea1-b27b-58679d67a14e",
          "label": "Contract",
          "name": "Mutual NDA - Acme Corp",
          "type": "Non-Disclosure Agreement"
        },
        {
          "id": "Company:acme incorporated",
          "label": "Company",
          "name": "Acme Inc.",
          "normalized_name": "Acme Incorporated"
        }
      ],
      "relationships": [
        {
          "source": "Company:acme incorporated",
          "target": "Contract:8f03c05c-efbc-4ea1-b27b-58679d67a14e",
          "type": "PARTY_TO"
        }
      ],
      "edges": [
        {
          "source": "Company:acme incorporated",
          "target": "Contract:8f03c05c-efbc-4ea1-b27b-58679d67a14e",
          "type": "PARTY_TO"
        }
      ]
    }
    ```

#### 18. Sync Contract to Knowledge Graph
* **METHOD**: `POST`
* **PATH**: `/api/v1/contracts/{contract_id}/sync-graph`
* **PURPOSE**: Extract contract entities, clauses, obligations, and risks from relational tables and populate Knowledge Graph nodes and relationships.

#### 19. Find Contracts by Company
* **METHOD**: `GET`
* **PATH**: `/api/v1/graph/contracts-by-company?company_name=Acme`
* **PURPOSE**: Graph query retrieving all contracts involving a company.

#### 20. Find Contracts by Jurisdiction
* **METHOD**: `GET`
* **PATH**: `/api/v1/graph/contracts-by-jurisdiction?jurisdiction_name=California`
* **PURPOSE**: Graph query retrieving contracts governed by a specified jurisdiction.

---

### HEALTH CHECK

#### 21. System Health Status
* **METHOD**: `GET`
* **PATH**: `/api/v1/health` and `/health`
* **PURPOSE**: Health check and connectivity diagnostics.
* **RESPONSE**:
  ```json
  {
    "status": "ok",
    "service": "Legal AI Contract Intelligence API",
    "version": "1.0.0",
    "environment": "development",
    "timestamp": "2026-09-06T06:30:00.000Z",
    "database": {
      "status": "connected",
      "dialect": "sqlite",
      "database": "legal_ai.db"
    }
  }
  ```
