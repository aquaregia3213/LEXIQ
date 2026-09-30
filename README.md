# LEXIQ — Agentic AI Legal Contract Intelligence Platform

<p align="center">
  <img src="https://img.shields.io/badge/Agentic%20AI-Autonomous%20ReAct-6366f1?style=for-the-badge&logo=openai" alt="Agentic AI" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-15.5-black?style=for-the-badge&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/Pytest-115%20Passing-success?style=for-the-badge&logo=pytest" alt="Tests" />
</p>

---

## 🌟 Overview

**LEXIQ** is an enterprise-grade **Agentic AI Legal Tech Platform** designed to analyze complex contract repositories. Unlike standard chatbots or single-step RAG pipelines, LEXIQ features an **autonomous ReAct Agent Orchestrator** equipped with **10 specialized tools** capable of multi-hop legal reasoning, knowledge graph traversal, cross-contract differencing, risk auditing, and zero-hallucination source citation.

---

## 🚀 Key Architectural Capabilities

- 🤖 **Autonomous Agentic AI (ReAct Loop)**: Plans multi-step analysis, inspects intermediate tool outputs, selects follow-up tools dynamically, and synthesizes answers strictly grounded in verifiable contract chunks.
- 🔍 **Hybrid RAG & Vector Search**: High-dimensional semantic embeddings combined with clause taxonomy filtering.
- 🕸️ **Knowledge Graph Traversal**: Relational graph modeling contracts, entities (Companies, Jurisdictions, Signers), obligations, and clauses using Cypher queries.
- ⚖️ **Automated Risk Analysis**: Calibrated severity detection identifying uncapped liability, non-compete overreaches, indefinite confidentiality, and one-sided indemnification clauses.
- 📑 **Cross-Contract Comparison**: Automated diffing of termination provisions, governing laws, and liability terms across distinct contracts with dual-contract citations.
- 🛡️ **Prompt Injection Resistance**: Isolated `<untrusted_contract_evidence>` execution boundaries neutralizing indirect prompt injection attacks embedded inside contract text.
- 🎯 **Zero-Hallucination Safe Refusal**: Strict evidence sufficiency gate returning transparent refusal and low confidence when source proof is absent.

---

## 🏛️ System Architecture

```mermaid
graph TD
    User([User / Web UI]) -->|Query| Route[POST /api/v1/agent/query]
    Route --> Orch[Agent Orchestrator: Planning & State]
    
    subgraph "Agentic Tool Registry"
        T1[search_contract]
        T2[get_clauses]
        T3[get_risks]
        T4[get_entities]
        T5[get_obligations]
        T6[query_knowledge_graph]
        T7[compare_contracts]
        T8[retrieve_source]
        T9[get_contract]
        T10[sync_knowledge_graph]
    end
    
    Orch --> T1 & T2 & T3 & T4 & T5 & T6 & T7 & T8
    
    subgraph "Core Data & Intelligence Engines"
        DB[(PostgreSQL / SQLite)]
        KG[(Neo4j Knowledge Graph)]
        VEC[ChromaDB / Vector Embeddings]
        EXT[Entity & Obligation Extractor]
        CLS[Taxonomy Clause Classifier]
        RSK[Risk Analyzer Engine]
    end
    
    T1 & T8 --> VEC
    T2 & T5 --> CLS
    T3 --> RSK
    T4 & T5 --> EXT
    T6 & T10 --> KG
    T7 & T9 --> DB
    
    Orch --> Agg[Evidence Aggregation & Sanitization]
    Agg --> Final[Grounded Answer + Findings + Citations + Confidence]
    Final --> User
```

---

## 📊 Quantitative Evaluation Benchmarks

Benchmarked across 7 end-to-end evaluation scenarios (`tests/evaluation/test_agent_benchmarks.py`):

| Evaluation Metric | Benchmark Target | Measured Result | Status |
| :--- | :---: | :---: | :---: |
| **Tool Selection Accuracy** | $\ge 90.0\%$ | **100.0%** (7/7 correct tool sequences) | ✅ **PASSED** |
| **Task Completion Rate** | $\ge 95.0\%$ | **100.0%** (7/7 tasks completed) | ✅ **PASSED** |
| **Evidence Grounding Rate** | $100.0\%$ | **100.0%** (All claims grounded in chunks) | ✅ **PASSED** |
| **Citation Correctness** | $100.0\%$ | **100.0%** (Valid document and page citations) | ✅ **PASSED** |
| **Hallucination Rate** | $0.0\%$ | **0.0%** (Zero fabricated claims) | ✅ **PASSED** |
| **Failure Handling Rate** | $100.0\%$ | **100.0%** (Graceful refusal on absent data) | ✅ **PASSED** |
| **Average Tool Calls per Task** | $\ge 2.0$ | **3.14 tool calls / query** | ✅ **PASSED** |
| **Average Execution Time** | $< 500$ ms | **11.1 ms** (In-memory execution) | ✅ **PASSED** |
| **Successful Multi-Step Tasks** | $100.0\%$ | **100.0%** (4/4 multi-step tasks verified) | ✅ **PASSED** |

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with pgvector (falls back gracefully to SQLite `legal_ai.db` in dev)
- **Knowledge Graph**: Neo4j (falls back to in-memory graph driver)
- **Vector Search / Embeddings**: Abstracted embedding service with deterministic semantic matching
- **Testing**: Pytest (115/115 passing tests across unit, integration, API, and e2e)

### Frontend
- **Framework**: Next.js 15 (App Router, React 19)
- **Language**: TypeScript 5.0+
- **Styling**: Vanilla CSS design tokens with sleek dark mode and glassmorphism
- **Components**: AI Analyst Agent View, Contract Detail Inspector, Clause Classifier, Risk Flags Feed, Knowledge Graph Visualizer

---

## ⚡ Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+** and `npm`

### 2. Clone the Repository
```bash
git clone https://github.com/aquaregia3213/LEXIQ.git
cd LEXIQ
```

### 3. Setup Backend
```bash
# Create and activate virtual environment (optional)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

### 4. Setup Frontend
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
- Frontend Web App: `http://localhost:3000`

---

## 🧪 Running the Test Suites

LEXIQ includes a comprehensive test suite of 115 tests:

```bash
# Run all tests
python -m pytest

# Run Agentic AI evaluation benchmarks with observable traces
python -m pytest tests/evaluation/test_agent_benchmarks.py -s

# Run API integration tests
python -m pytest tests/api/test_agent_api.py tests/api/test_api_v1.py
```

---

## 📁 Project Structure

```text
LEXIQ/
├── backend/
│   └── app/
│       ├── agents/              # Autonomous ReAct Agent & 10 Specialized Tools
│       │   ├── orchestrator.py  # Planning, Tool Execution, Re-planning Loop
│       │   ├── prompts.py       # Prompt Injection Defense & Safety Framing
│       │   ├── schemas.py       # Pydantic Schemas for Agent Requests/Responses
│       │   ├── state.py         # Step-by-step Trace & Evidence Tracking
│       │   └── tools/           # 10 Agent Tools
│       ├── api/                 # FastAPI REST Endpoints (/agent, /contracts, /search, etc.)
│       ├── models/              # SQLAlchemy Database Models
│       └── services/            # Extractor, Clause Classifier, Risk Analyzer, Graph
├── frontend/                    # Next.js 15 Dark-Mode Web App
│   ├── app/                     # Next.js App Router Pages
│   ├── components/              # UI Components (AI Analyst, ContractDetails, Sidebar)
│   └── lib/                     # Typed API Client & Data Models
├── tests/                       # 115 Test Cases
│   ├── api/                     # REST Endpoint Integration Tests
│   ├── evaluation/              # 7 Agentic AI Benchmark Tasks & Metrics
│   └── unit/                    # Pipeline, Chunking, Extraction, Graph Unit Tests
├── docs/                        # Complete Architecture & Evaluation Documentation
│   └── AGENTIC_AI_EVALUATION_REPORT.md
└── README.md
```

---

## ⚖️ Legal Disclaimer

LEXIQ is an AI-assisted contract intelligence tool developed for portfolio and educational demonstration purposes. Outputs generated by the AI Analyst do **not** constitute formal legal counsel. All critical contractual determinations should be reviewed by qualified legal counsel.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).