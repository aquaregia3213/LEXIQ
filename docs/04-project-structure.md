# Project Structure

## Recommended Structure

```text
legal-ai-contract-intelligence/
│
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   │
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   │
│   └── tests/
│
├── ingestion/
│   ├── parsers/
│   ├── chunking/
│   ├── preprocessing/
│   └── pipeline/
│
├── ai/
│   ├── embeddings/
│   ├── extraction/
│   ├── classification/
│   ├── rag/
│   ├── summarization/
│   └── risk_analysis/
│
├── knowledge_graph/
│   ├── models/
│   ├── queries/
│   └── services/
│
├── database/
│   ├── migrations/
│   └── seeds/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── types/
│
├── evaluation/
│   ├── datasets/
│   ├── metrics/
│   └── experiments/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
│
├── docs/
│
└── prompts/
```

## Directory Responsibilities

### backend/

Contains the FastAPI application.

It should handle:

- API routes
- authentication
- request validation
- orchestration
- service integration

### ingestion/

Responsible for:

- PDF parsing
- DOCX parsing
- OCR
- text cleaning
- structure detection
- chunking

### ai/

Contains AI-specific logic.

Do not place API route logic here.

### knowledge_graph/

Contains:

- Neo4j connection logic
- graph creation
- Cypher queries
- graph retrieval

### database/

Contains:

- migrations
- seed data
- database-specific setup

### frontend/

Contains the user interface.

### evaluation/

Contains experiments and evaluation datasets.

### tests/

Contains automated tests.

## Code Organization Rule

Business logic must not be duplicated across API endpoints.

Prefer reusable services.

## Naming Rules

Use:

- `snake_case` for Python files
- descriptive names
- small modules
- explicit function names

Avoid:

- `utils2.py`
- `final.py`
- `new_service.py`
- giant files containing unrelated functionality

## Dependency Rule

Prefer:

```text
API
 ↓
Service
 ↓
Repository/Database
```

rather than:

```text
API
 ↓
Database + LLM + Neo4j + random business logic
```

## AI Module Rule

LLM calls should be centralized through reusable services rather than scattered throughout the codebase.

This makes model replacement, testing, logging, and cost tracking easier.