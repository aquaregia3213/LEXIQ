# System Architecture

## High-Level Architecture

```text
                    ┌────────────────────┐
                    │      Frontend      │
                    │     Next.js        │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │     FastAPI        │
                    │      Backend       │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
      ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
      │ Document    │  │ AI/NLP      │  │ Retrieval   │
      │ Processing  │  │ Pipeline    │  │ Pipeline    │
      └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
             │                │                │
             └────────────────┼────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       PostgreSQL         pgvector          Neo4j
       Metadata/Data      Embeddings       Knowledge Graph
                              │
                              ▼
                            LLM
```

## Processing Pipeline

```text
Document Upload
      ↓
File Validation
      ↓
Document Parsing
      ↓
Text Cleaning
      ↓
Structure Detection
      ↓
Chunking
      ↓
Entity Extraction
      ↓
Clause Extraction
      ↓
Clause Classification
      ↓
Embedding Generation
      ↓
Vector Storage
      ↓
Knowledge Graph Construction
```

## Query Pipeline

```text
User Query
    ↓
Query Understanding
    ↓
Query Embedding
    ↓
Vector Retrieval
    ↓
Metadata Filtering
    ↓
Optional Graph Retrieval
    ↓
Context Construction
    ↓
LLM
    ↓
Grounded Answer
    ↓
Source References
```

## Architectural Principles

### Modularity

Each major AI component should be independently replaceable.

### Separation of Concerns

Document processing, retrieval, graph operations, LLM operations, and API logic should not be tightly coupled.

### Evidence First

AI outputs must be based on retrieved evidence.

### MVP First

Avoid building complex infrastructure before proving the core workflow.

## Storage Responsibilities

### PostgreSQL

Use for:

- users
- contracts
- document metadata
- processing jobs
- clause records
- entity records
- risk records

### pgvector

Use for:

- embeddings
- semantic retrieval

### Neo4j

Use for:

- entity relationships
- graph traversal
- cross-contract relationships

## Vector Search vs Knowledge Graph

Vector search answers:

> "What text is semantically similar to this query?"

Knowledge graphs answer:

> "How are these entities and concepts related?"

RAG can combine both when the query benefits from semantic evidence and structured relationships.

## Failure Handling

Each processing stage should have clear failure states.

Example:

```text
UPLOADED
PROCESSING
PARSED
INDEXED
COMPLETED
FAILED
```

Failed processing should record an error without corrupting existing data.

## Architecture Rule

Do not add microservices, message brokers, Kubernetes, or other infrastructure unless the project genuinely requires them.

For the student MVP, a modular monolith is preferred.