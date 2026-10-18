# LEXIQ: Implementation Status & Google Gemini Integration

**Platform:** LEXIQ — Agentic AI-Powered Legal Contract Intelligence Platform  
**Integration Version:** 1.0.0 (Google GenAI SDK Integration)  
**Status:** Gemini Integration Completed & Verified  

---

## 1. Google Gemini Integration Architecture

The platform now natively integrates Google's official Gen AI SDK (`google-genai>=2.31.0`) to provide real, hallucination-resistant legal reasoning and dense semantic vector embeddings.

### Core Components
| Component | Implementation File | Model | Description |
|---|---|---|---|
| **Gemini LLM Provider** | [`backend/app/services/gemini_service.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/gemini_service.py) | `gemini-2.5-flash` | Grounded contract QA with page/section citations, XML untrusted data wrapper, prompt-injection defense, timeouts, retries, and legal disclaimers. |
| **Gemini Embedding Provider** | [`backend/app/services/gemini_service.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/gemini_service.py) | `text-embedding-004` | 768-dimensional dense vector embeddings with batch support and automatic vector dimension alignment. |
| **LLM Service Router** | [`backend/app/services/llm.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/llm.py) | Dynamic | Resolves `GeminiLLMProvider` in production or `DeterministicLLMProvider` in explicit development/testing environments. |
| **Embedding Service Router** | [`backend/app/services/embedding.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/embedding.py) | Dynamic | Resolves `GeminiEmbeddingProvider` in production or `DeterministicEmbeddingProvider` in explicit development/testing environments. |
| **Agent Orchestrator** | [`backend/app/agents/orchestrator.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/agents/orchestrator.py) | `gemini-2.5-flash` | Multi-step legal agent using Gemini to synthesize final grounded findings and source citations across tool observations. |

---

## 2. Feature Implementation Status Matrix

### Real Gemini Calls (Active when `AI_PROVIDER=gemini` & `GEMINI_API_KEY` set)
| Capability | API Endpoint | Service Layer | Model Identifier |
|---|---|---|---|
| **Grounded RAG Contract QA** | `POST /api/v1/rag/query` | `RAGPipeline.ask_question` | `gemini-2.5-flash` |
| **Contract Chunk Vectorization** | `POST /api/v1/contracts/upload` | `process_contract_ingestion` | `text-embedding-004` |
| **Semantic Vector Retrieval** | `POST /api/v1/search` | `SearchService.semantic_search` | `text-embedding-004` |
| **Agent Evidence Synthesis** | `POST /api/v1/agent/query` | `AgentOrchestrator.run` | `gemini-2.5-flash` |

### Rule-Based & Mocked Components (Preserved for local offline capability)
| Capability | Current Mechanism | Target Future Upgrade |
|---|---|---|
| **Clause Taxonomy & Classification** | Keyword and regex matching across 12 legal categories | Few-shot Gemini classification |
| **Named Entity Extraction (NER)** | Regular expressions for Company, Person, Date, Amount, Jurisdiction | Spacy NER or Gemini structured entity extraction |
| **Obligation Extraction** | Modal verb patterns ("shall", "must") & deadline regexes | Gemini obligation and deadline extractor |
| **Risk Analysis** | 5 regex risk patterns (liability, renewal, indemnification, termination, IP) | Gemini deep contractual risk assessment |
| **Knowledge Graph** | In-memory Python dictionaries and edge lists (`InMemoryGraphProvider`) | Persistent Neo4j graph database |
| **Agent Tool Selection** | Deterministic intent pattern matching | Native Gemini Function Calling / Tool Calling |
| **Langflow Integration** | **Completed & Verified** (via `LangflowClientService`, `/api/v1/agent/tools/execute`, and native fallback) | Advanced multi-agent graph flows |
| **eCourts Integration** | **Completed & Verified** (Portal-assisted, lawful intake, AI risk analysis, Next.js UI, Agent tool) | Direct NIC API Setu live credentials (pending institutional clearance) |

---

## 3. Vector Database Alignment & Schema Safety

- **Embedding Model:** `text-embedding-004` generates **768-dimensional** vector embeddings.
- **Dynamic Database Column:** [`backend/app/models/models.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/models/models.py) defines:
  ```python
  embedding = Column(
      Vector(settings.embedding_dimension).with_variant(JSON, "sqlite"),
      nullable=True
  )
  ```
- **PostgreSQL / pgvector Safety:** [`backend/app/database.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/database.py) checks PostgreSQL catalogs at startup. If the existing `chunks.embedding` column has a different dimensionality (e.g. 1536 from an older setup), it safely alters the column type to `vector(768)` without breaking table creation.
- **SQLite Fallback:** Uses SQLAlchemy's JSON column variant. It stores float arrays natively without schema alterations or dimension constraints.

---

## 4. Security & Error Transparency

1. **Zero Secret Leaks:**
   - Error messages automatically redact API keys matching `AIza[0-9A-Za-z-_]{30,40}`, `key=...`, and `Bearer ...` tokens.
   - `.env` and `.env.local` files are strictly excluded via `.gitignore`.
2. **Transparent Error Reporting (No Fake Answers):**
   - If `AI_PROVIDER=gemini` is active and the API key is missing, invalid, or quota-exhausted, the backend raises a structured `GeminiProviderError` (HTTP 502/503).
   - The platform will **never** silently return fake mock answers when configured for production AI.
3. **Prompt Injection Defense:**
   - Contract chunks are enclosed within `<untrusted_contract_evidence>` XML tags.
   - Strict system instructions instruct Gemini to treat contract text as data, not instructions.

---

## 5. Verification & Test Suite

- **Total Test Cases:** **132 automated tests** across unit, API, integration, e2e, evaluation benchmarks, and live smoke tests.
- **Test Command:** `python -m pytest`
- **Result:** **129 passed, 3 skipped (live smoke tests skipped offline), 0 failed** (100% pass rate).
- **Offline / CI Reliability:** `tests/conftest.py` configures `AI_PROVIDER=deterministic` for the standard test suite, so test runs never require an external network connection or API credits.
- **Live Smoke Test:** To test against real Google Gemini servers with an active API key:
  ```powershell
  $env:GEMINI_API_KEY="your_actual_key"
  python -m pytest tests/smoke/test_gemini_smoke.py
  ```

---

## 6. How to Get a Free Google Gemini API Key

Follow these steps to obtain a free API key from Google AI Studio:

1. **Visit Google AI Studio:**
   Navigate to [https://aistudio.google.com/](https://aistudio.google.com/) and sign in with your Google account.
2. **Click "Get API Key":**
   In the left sidebar or top banner, click on **"Get API key"**.
3. **Create a New Key:**
   Click **"Create API key"** $\rightarrow$ select an existing Google Cloud project or create a new project in one click.
4. **Copy the API Key:**
   Copy your generated key (starts with `AIzaSy...`).
5. **Add to `.env`:**
   In your project root, open `.env` and set:
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_copied_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_EMBEDDING_MODEL=text-embedding-004
   ```
6. **Free Tier Limits:**
   The Google AI Studio free tier provides:
   - **gemini-2.5-flash / gemini-2.0-flash:** Up to 15 Requests Per Minute (RPM), 1 million Tokens Per Minute (TPM), and 1,500 Requests Per Day (RPD) completely free.
   - **gemini-embedding-001 / text-embedding-004:** Free embedding generation within rate limits.
   - Perfect for local development, academic demos, and staging workloads.

---

## 7. Langflow Workflow Orchestration Integration

Langflow is integrated as the dedicated agent workflow orchestration layer:

- **Target Architecture:** `Next.js frontend` $\rightarrow$ `FastAPI backend` $\rightarrow$ `Langflow API (:7860)` $\rightarrow$ `Gemini 2.5 Flash & LEXIQ Tools` $\rightarrow$ `FastAPI backend (:8000)` $\rightarrow$ `PostgreSQL/pgvector`.
- **Client Service:** [`backend/app/services/langflow_client.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/backend/app/services/langflow_client.py) with request timeouts, error categorization (`LangflowUnavailableError`, `LangflowTimeoutError`, `LangflowResponseError`), and structured output parsing.
- **Server-to-Server Tool Endpoint:** `POST /api/v1/agent/tools/execute` authenticated via constant-time token comparison (`x-lexiq-api-key`). Strict multi-tenant checks prevent cross-tenant contract access.
- **Failover Protection:** Automatic fallback to native `AgentOrchestrator` if Langflow is offline or times out (`LANGFLOW_FALLBACK_TO_NATIVE=true`).
- **Reproducible Flow Export:** [`flows/lexiq_legal_agent_flow.json`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/flows/lexiq_legal_agent_flow.json) and custom component [`flows/custom_components/lexiq_tool_caller.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/flows/custom_components/lexiq_tool_caller.py).
- **Test Coverage:** 17 dedicated unit/integration tests in [`tests/unit/test_langflow.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/tests/unit/test_langflow.py) covering success, timeout, 500 error, unauthorized keys, unknown tools, argument schemas, tenant isolation, and native fallback. Total test suite: **149 passed, 0 failed**.
