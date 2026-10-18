# LEXIQ: Implementation Audit & Architecture Review

**Platform:** LEXIQ — Agentic AI-Powered Legal Contract Intelligence Platform  
**Audit Date:** October 2026  
**Auditor Role:** Senior Software Architect  
**Status:** Audit Completed (No Source Files Modified)

---

## 1. Executive Summary

This audit assesses the current state of **LEXIQ**, an enterprise legal contract intelligence platform designed for contract ingestion, chunking, semantic retrieval, clause extraction, obligation tracking, risk analysis, knowledge graph traversal, and agentic AI query orchestration.

### Key Audit Findings:
1. **Fully Functional Local Core (Mocked/Deterministic AI):** The application has a functional end-to-end pipeline with Next.js frontend, FastAPI backend, SQLite/PostgreSQL storage, document parsing (PDF/DOCX), section-aware chunking, rule-based extraction, and an in-memory graph.
2. **Deterministic & Simulated AI Layer:** All AI capabilities (LLM generation, semantic embeddings, knowledge graph, and agent orchestration) currently use **deterministic, heuristic, or in-memory mock implementations**.
   - Embeddings use an MD5 word/subword n-gram hash projection into a 1536-dimensional unit vector.
   - LLM generation uses keyword/stop-word overlap matching.
   - Agent orchestration uses a deterministic regex-driven ReAct state machine with hand-coded decision rules.
   - Knowledge Graph uses in-memory Python dictionaries and lists.
3. **Missing Integrations:**
   - **Langflow:** Does **not** exist in the repository (0 references).
   - **Google Gemini:** Does **not** exist in the repository (0 references).
   - **Real Embedding Models (Gemini / OpenAI / HuggingFace):** Do **not** exist in active code.
   - **eCourts Integration:** Does **not** exist in the repository (0 references).
4. **Test Suite Baseline:** 115 automated tests (`pytest`) currently pass (100% pass rate), verifying existing contracts, routes, extractors, search, and agent benchmarks. Any architectural upgrade must preserve test compatibility and existing APIs.

---

## 2. Existing Architecture Overview

```
                          ┌────────────────────────────────────────┐
                          │         Next.js 15 Frontend            │
                          │   (React 19, TypeScript, Vanilla CSS)   │
                          │        Runs on http://localhost:3000   │
                          └───────────────────┬────────────────────┘
                                              │ HTTP / JSON (REST API)
                                              ▼
                          ┌────────────────────────────────────────┐
                          │          FastAPI Backend App           │
                          │   (app/main.py, v1 & legacy routers)   │
                          │        Runs on http://localhost:8000   │
                          └──────┬────────────┬─────────────┬──────┘
                                 │            │             │
                 ┌───────────────┘            │             └────────────────┐
                 ▼                            ▼                              ▼
    ┌───────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
    │   Ingestion Engine    │   │     AI & Agent Core       │   │    Storage & Knowledge    │
    │  - PyMuPDF (PDF)      │   │  - AgentOrchestrator      │   │  - SQLAlchemy 2.0 ORM     │
    │  - python-docx (DOCX) │   │  - 10 Analysis Tools      │   │  - PostgreSQL / pgvector  │
    │  - Text cleaner       │   │  - RAG Pipeline           │   │    (SQLite fallback)      │
    │  - Semantic Chunker   │   │  - Rule Extractors        │   │  - InMemoryGraphProvider  │
    │  - Upload validator   │   │  - Deterministic Provider │   │    (Neo4j not hooked up)  │
    └───────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
```

---

## 3. Important File Paths and Responsibilities

### 3.1 Backend Entry Points & Core Infrastructure
| File Path | Responsibility |
|---|---|
| [`backend/app/main.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/main.py) | Application entry point: FastAPI app factory, CORS configuration, exception handlers, v1 router mounting, legacy router mounting, and `/health` route. |
| [`backend/app/config.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/config.py) | Environment settings via Pydantic `BaseSettings`. Loads `.env`, defines database URLs, provider names, and CORS origins. |
| [`backend/app/database.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/database.py) | SQLAlchemy engine creation, session factory (`SessionLocal`), database connection checks, and automatic fallback from PostgreSQL to `sqlite:///legal_ai.db`. |
| [`backend/app/models/models.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/models/models.py) | Relational database ORM models: `User`, `Contract`, `Document`, `Clause`, `Entity`, `Obligation`, `RiskFlag`, `Chunk` (with pgvector `Vector(1536)` / SQLite `JSON` variant). |
| [`backend/app/api/v1.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/api/v1.py) | REST API v1 router prefixing `/api/v1` and bundling all modular routes. |
| [`backend/app/api/dependencies.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/api/dependencies.py) | Dependency injection providers for database session, RAG pipeline, and services. |

### 3.2 Ingestion Engine
| File Path | Responsibility |
|---|---|
| [`ingestion/pipeline/ingestor.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/ingestion/pipeline/ingestor.py) | Main upload orchestration: file persistence to `uploads/contracts/`, DB record creation, parser dispatch, chunking, embedding generation, and status commits. |
| [`ingestion/parsers/pdf_parser.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/ingestion/parsers/pdf_parser.py) | PyMuPDF (`fitz`) text extraction per page with whitespace cleanup. |
| [`ingestion/parsers/docx_parser.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/ingestion/parsers/docx_parser.py) | `python-docx` extraction across paragraphs and tables with estimated page splitting. |
| [`ingestion/chunking/chunker.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/ingestion/chunking/chunker.py) | Semantic section-aware document chunker with regex header detection, character budgeting, and metadata enrichment. |
| [`ingestion/preprocessing/cleaner.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/ingestion/preprocessing/cleaner.py) | Text sanitization and whitespace normalization. |
| [`ingestion/preprocessing/validator.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/ingestion/preprocessing/validator.py) | Upload validation: mime-types, file sizes, and empty-content prevention. |

### 3.3 AI Services & Agent Orchestration
| File Path | Responsibility |
|---|---|
| [`backend/app/agents/orchestrator.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/agents/orchestrator.py) | Multi-step ReAct agent orchestrator: regex intent parsing, tool selection, evidence verification, and answer assembly. |
| [`backend/app/agents/tools/`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/agents/tools/) | 10 modular legal agent tools: `search_tool`, `contract_tool`, `clause_tool`, `entity_tool`, `obligation_tool`, `risk_tool`, `graph_tool`, `source_tool`, `comparison_tool`. |
| [`backend/app/services/embedding.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/embedding.py) | Embedding abstraction: `BaseEmbeddingProvider`, `DeterministicEmbeddingProvider` (MD5 subword hash, 1536 dimensions), and `EmbeddingService`. |
| [`backend/app/services/llm.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/llm.py) | LLM abstraction: `BaseLLMProvider`, `DeterministicLLMProvider` (stop-word filtering, text matching), and `LLMService`. |
| [`backend/app/services/search.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/search.py) | Vector retrieval service: loads chunks and computes cosine similarity in Python. |
| [`backend/app/services/rag.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/rag.py) | RAG pipeline: vector search, XML prompt packaging, grounded answer generation, and evidence checks. |
| [`backend/app/services/clause_classifier.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/clause_classifier.py) | Clause taxonomy classification across 12 legal categories using pattern matching and keyword weighting. |
| [`backend/app/services/extractor.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/extractor.py) | Regex and rule-based Named Entity Recognition (NER) for Company, Person, Date, Amount, Jurisdiction. |
| [`backend/app/services/obligation_extractor.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/obligation_extractor.py) | Pattern-based extraction of contractual obligations, parties, and temporal deadlines. |
| [`backend/app/services/risk_analyzer.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/risk_analyzer.py) | Rule-based risk flag detection for renewal, liability caps, indemnification, termination, and IP. |
| [`backend/app/services/graph.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/graph.py) | Knowledge Graph service: `InMemoryGraphProvider` storing nodes and edges in Python data structures. |

### 3.4 Frontend Entry Points & Views
| File Path | Responsibility |
|---|---|
| [`frontend/app/layout.tsx`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/frontend/app/layout.tsx) | Root layout, metadata, Inter font imports. |
| [`frontend/app/page.tsx`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/frontend/app/page.tsx) | Primary single-page app shell managing active view state, dark/light theme, and health polling. |
| [`frontend/lib/api.ts`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/frontend/lib/api.ts) | Centralized TypeScript API client consuming all `/api/v1` backend endpoints. |
| [`frontend/components/views/`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/frontend/components/views/) | 11 comprehensive views: `DashboardView`, `ContractUploadView`, `ContractListView`, `ContractDetailsView`, `AgentView`, `SemanticSearchView`, `RAGQuestionView`, `ClauseView`, `EntityView`, `RiskAnalysisView`, `SourceEvidenceView`. |
| [`frontend/components/KnowledgeGraphViewer.tsx`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/frontend/components/KnowledgeGraphViewer.tsx) | Canvas-based dynamic 2D/3D knowledge graph visualizer with zoom/pan and node inspection. |

---

## 4. End-to-End Execution Flow Tracing

### 4.1 Contract Upload & Ingestion Flow
1. **Request:** Frontend sends `multipart/form-data` containing `file` (`.pdf` or `.docx`), optional `contract_name`, and optional `contract_type` to `POST /api/v1/contracts/upload`.
2. **Validation:** In `contracts.py`, file extension is validated against `[.pdf, .docx]` and content length > 0.
3. **Storage & Records:** In `ingestion/pipeline/ingestor.py`:
   - Unique file name generated (`{uuid}.{ext}`) and saved into `uploads/contracts/`.
   - Initial database records created: `Contract` (`status="PROCESSING"`) and `Document` (`processing_status="PROCESSING"`).
4. **Parsing:**
   - PDF: Parsed by PyMuPDF (`fitz`), iterating pages and cleaning text.
   - DOCX: Parsed by `python-docx`, iterating paragraphs and table rows.
5. **Chunking:** `chunk_document_pages` checks for section headings (e.g., `ARTICLE`, `SECTION`, `CONFIDENTIALITY`), divides text into chunks <= 1000 chars with 150-char overlap, and tags chunks with start/end page numbers.
6. **Vectorization:** `get_embedding_service().embed_text(chunk_text)` computes a 1536-dimensional vector for each chunk.
7. **Commit:** `Chunk` rows with embeddings and JSON metadata are saved to DB. Contract status updated to `COMPLETED`.

### 4.2 Semantic Retrieval Flow
1. **Request:** Client calls `POST /api/v1/search` with `{ "query": "...", "contract_id": "...", "top_k": 5 }`.
2. **Query Vector:** `SearchService` generates vector embedding for the query string using `embedding_service.embed_text(query)`.
3. **Database Query:** SQLAlchemy loads `Chunk` entities joined with `Contract` and `Document` matching optional metadata filters.
4. **In-Memory Cosine Similarity:** In `search.py`, cosine similarity is computed between query vector and each candidate chunk vector in Python.
5. **Sorting & Filtering:** Results are filtered by `min_score`, sorted descending by similarity, and returned with page numbers and section metadata.

### 4.3 Grounded RAG Question Answering Flow
1. **Request:** Client calls `POST /api/v1/rag/query` with `{ "question": "...", "contract_id": "..." }`.
2. **Retrieval:** `RAGPipeline.ask_question` invokes `search_service.semantic_search(top_k=5)`.
3. **Evidence Evaluation:**
   - If no chunks match, returns `INSUFFICIENT_EVIDENCE_RESPONSE` immediately.
4. **Prompt Assembly & Grounded Answering:**
   - Chunks are enclosed in `<untrusted_contract_evidence>` XML tags.
   - `llm_service.generate_grounded_answer` evaluates substantive query terms against chunk text, eliminates prompt injections, extracts supporting quotes, and formats citations.
5. **Output:** Returns answer text, verified source citations, and confidence disclaimer.

### 4.4 Agent Tool Selection and Execution Flow
1. **Request:** Client calls `POST /api/v1/agent/query` with `{ "question": "...", "contract_id": "..." }`.
2. **State Initialization:** `AgentOrchestrator` initializes `AgentState` with a step budget (max 5-10 steps).
3. **Intent Detection & Tool Dispatch Loop:**
   - Substring & regex checks inspect the question:
     - Comparison intent ("compare", "difference") $\rightarrow$ `compare_contracts` $\rightarrow$ `retrieve_source`
     - Termination + Obligations $\rightarrow$ `get_clauses` $\rightarrow$ `get_obligations` $\rightarrow$ `search_contract` $\rightarrow$ `retrieve_source`
     - Knowledge Graph / Party queries $\rightarrow$ `get_entities` $\rightarrow$ `query_knowledge_graph` $\rightarrow$ `retrieve_source`
     - Risk queries $\rightarrow$ `get_risks` $\rightarrow$ `get_clauses` $\rightarrow$ `retrieve_source`
     - Obligation queries $\rightarrow$ `get_obligations` $\rightarrow$ `retrieve_source`
     - Clause queries $\rightarrow$ `get_clauses` $\rightarrow$ `retrieve_source`
     - General questions $\rightarrow$ `search_contract` $\rightarrow$ `get_contract` $\rightarrow$ `retrieve_source`
4. **Execution:** Each tool runs against the database and records its observation and evidence in `AgentState`.
5. **Sufficiency Check:** Orchestrator verifies whether query terms are supported by collected evidence.
6. **Synthesis:** Answers are assembled exclusively from verified source citations, prompt-injection patterns are redacted, and mandatory legal safety disclaimers are appended.

---

## 5. Working vs. Mocked & Incomplete Features

| Feature | Implementation Status | Current Mechanism | Real Target Needed |
|---|---|---|---|
| **PDF/DOCX Document Ingestion** | **Working** | PyMuPDF & python-docx file parsing, text extraction, page tracking | Production OCR for scanned PDFs |
| **Document Chunking** | **Working** | Semantic section-aware chunker with regex header detection & overlap | Fully working |
| **PostgreSQL / pgvector Storage** | **Working (with SQLite fallback)** | SQLAlchemy models with pgvector `Vector(1536)` and SQLite `JSON` fallback | Fully working |
| **Vector Embedding Generation** | **Mocked / Deterministic** | MD5 subword hash projection into 1536-dim normalized vector | Google Gemini / OpenAI embeddings |
| **Semantic Retrieval** | **Working (In-Memory)** | In-memory Python cosine similarity over chunks | PostgreSQL pgvector native `<=>` cosine distance |
| **RAG Question Answering** | **Mocked / Deterministic** | Heuristic word overlap and quotation synthesis | Google Gemini LLM generation |
| **Agent Orchestrator** | **Mocked / Deterministic** | Regex & rule-based ReAct state loop | ReAct LLM Agent with tool calling |
| **Clause Extraction** | **Working (Rule-Based)** | Regex and keyword taxonomy across 12 clause categories | Few-shot LLM clause extraction |
| **Entity Extraction** | **Working (Rule-Based)** | Regex patterns for Company, Date, Amount, Jurisdiction | Spacy NER or LLM NER |
| **Obligation Extraction** | **Working (Rule-Based)** | Regex detection of modal verbs ("shall", "must") and deadlines | LLM obligation extraction |
| **Risk Analysis** | **Working (Rule-Based)** | Regex detection across 5 risk types with safety disclaimers | LLM risk analysis |
| **Knowledge Graph** | **Mocked / In-Memory** | `InMemoryGraphProvider` in Python memory | Neo4j database or Langflow graph |
| **Langflow Integration** | **Missing** | Not implemented (0 references) | Integration needed |
| **Google Gemini Integration** | **Missing** | Not implemented (0 references) | Integration needed |
| **eCourts Integration** | **Missing** | Not implemented (0 references) | Integration needed |
| **Frontend UI** | **Working** | Next.js 15, React 19, responsive dark/light themes, 11 interactive views | Fully working |

---

## 6. Security & Vulnerability Analysis

1. **Untrusted LLM Provider Keys:** `.env` and `.env.example` contain placeholder API keys (`your_llm_api_key_here`, `your_embedding_api_key_here`). No active private keys are committed in git.
2. **Prompt Injection Defenses:** The current implementation already implements prompt-injection stripping (e.g. `re.sub(r"(ignore previous instructions|system override|print secret)", ...)` and XML tag encapsulation `<untrusted_contract_evidence>`.
3. **Database Security:**
   - Raw SQL strings are avoided; SQLAlchemy ORM queries and parameterized expressions are used.
   - Deletions are cascaded cleanly across related tables (`ondelete="CASCADE"`).
4. **Physical File Lifecycle:**
   - Contract deletion (`DELETE /api/v1/contracts/{id}`) removes the physical uploaded file from disk.
   - Ingestion failures remove temporary uploaded files immediately to prevent disk clutter.
5. **CORS:** CORS allows localhost ports (`http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:5173`). In production, this should be restricted to verified domain names.

---

## 7. Integration Gaps & Breaking-Change Risks

### 7.1 Gap Analysis for Missing Technologies
1. **Google Gemini:**
   - Missing dependencies: `google-genai` / `google-generativeai`.
   - Need Gemini client adapter implementing `BaseLLMProvider` and `BaseEmbeddingProvider`.
2. **Langflow:**
   - No Langflow client, API endpoint, or visual workflow schema exists in the repository.
   - Langflow can be integrated to orchestrate the multi-agent contract review pipeline or serve as a visual RAG graph.
3. **eCourts Integration:**
   - No court data APIs, scraping scripts, or Indian eCourts / CNR lookup services exist.
   - Needs a dedicated service to fetch case records, judge orders, precedents, and court listing status by case number / CNR / party name.

### 7.2 Breaking-Change Risks
- **Test Suite Breakage:** The test suite contains 115 tests expecting exact deterministic output (e.g., hash vector numbers, specific keyword extractions, and hardcoded agent responses). If deterministic providers are outright replaced instead of wrapped with provider-switching logic (`LLM_PROVIDER=gemini` vs `LLM_PROVIDER=deterministic`), the test suite will fail.
- **Vector Dimensionality Mismatch:**
  - `Chunk.embedding` is declared as `Vector(1536)` for pgvector.
  - OpenAI `text-embedding-3-small` is 1536-dimensional.
  - Google Gemini `text-embedding-004` defaults to 768 dimensions (or supports output dimensionality parameter).
  - Changing embedding dimensions requires database migration or configurable vector size.
- **SQLite vs PostgreSQL Compatibility:**
  - SQLite does not have native pgvector support. The current architecture gracefully falls back to storing vector embeddings as JSON in SQLite and doing cosine similarity in Python. Any database-level pgvector operator (`<=>`) must maintain this SQLite fallback.

---

## 8. Exact Commands to Run and Test

### 8.1 Backend Execution
```powershell
# 1. Install Python dependencies
python -m pip install -r requirements.txt

# 2. (Optional) Run database seed script
python -m database.seeds.seed_data

# 3. Start the FastAPI development server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
Health endpoint: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 8.2 Frontend Execution
```powershell
# 1. Navigate to frontend directory and install dependencies
cd frontend
npm install

# 2. Run the Next.js development server
npm run dev

# 3. Run frontend linter
npm run lint
```
Frontend web application: [http://localhost:3000](http://localhost:3000)

> [!NOTE]
> `npm run lint` currently reports strict ESLint warnings/errors (primarily `@typescript-eslint/no-explicit-any` and unescaped quotes in JSX text). The Next.js dev server runs cleanly, but lint rules should be addressed before production static bundle builds.


### 8.3 Running Automated Tests
```powershell
# Run complete test suite (115 tests)
python -m pytest

# Run specific test modules
python -m pytest tests/api/test_agent_api.py
python -m pytest tests/evaluation/test_agent_benchmarks.py
python -m pytest tests/unit/test_rag.py
```

---

## 9. Recommended Implementation Order for Upgrades

To upgrade LEXIQ to enterprise agentic intelligence without breaking existing features or tests:

1. **Phase 1: Real Embedding & LLM Provider Adapter (Google Gemini & OpenAI)**
   - Add `google-genai` and `openai` to `requirements.txt`.
   - Implement `GeminiLLMProvider` and `GeminiEmbeddingProvider` conforming to `BaseLLMProvider` and `BaseEmbeddingProvider`.
   - Support configurable dimensionality and keep `DeterministicLLMProvider` and `DeterministicEmbeddingProvider` as defaults when no API key is provided (ensuring 100% test pass rate).
2. **Phase 2: Real Agent Tool Calling (Gemini Function Calling)**
   - Upgrade `AgentOrchestrator` to use native Gemini function calling / tool calling alongside the existing deterministic fallback.
3. **Phase 3: Langflow Pipeline Orchestration**
   - Implement Langflow bridge/service for visual agentic workflow orchestration.
4. **Phase 4: eCourts Integration**
   - Create an eCourts service client (`backend/app/services/ecourts.py`) to search CNR numbers, case status, hearing dates, and past court precedents.
   - Add an eCourts agent tool (`ECourtsSearchTool`) to `backend/app/agents/tools/`.
   - Add frontend eCourts lookup view.
5. **Phase 5: Neo4j Knowledge Graph Connector**
   - Implement `Neo4jGraphProvider` conforming to `BaseGraphProvider` for true persistent graph traversal.
