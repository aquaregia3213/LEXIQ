# MVP Scope

## Objective

Build the smallest version that demonstrates the core value of the platform.

## MVP Features

### 1. Contract Upload

Support:

- PDF
- DOCX

### 2. Document Parsing

Extract:

- text
- pages
- basic structure

### 3. Chunking

Create searchable chunks with metadata.

### 4. Embeddings

Generate embeddings and store them in pgvector.

### 5. Semantic Search

Allow natural-language searches.

### 6. Basic RAG

Allow users to ask questions about contracts.

### 7. Entity Extraction

Extract major entities.

### 8. Clause Extraction

Identify major clause categories.

### 9. Basic Risk Detection

Detect a limited set of obvious risks.

### 10. Source Evidence

Show the document and page/chunk supporting the result.

## MVP Architecture

```text
Frontend
   ↓
FastAPI
   ↓
Document Processing
   ↓
PostgreSQL + pgvector
   ↓
RAG
   ↓
LLM
```

Neo4j may be introduced immediately after the MVP core pipeline is stable.

## Not MVP

Do not initially build:

- multi-agent systems
- fine-tuned models
- Kubernetes
- microservices
- advanced OCR
- automatic contract redlining
- automated legal advice
- enterprise SSO
- massive distributed processing

## Version 2

Add:

- Neo4j knowledge graph
- hybrid graph + vector retrieval
- improved risk detection
- advanced clause comparison
- contract analytics

## Version 3

Potential features:

- multi-user access
- advanced permissions
- enterprise authentication
- contract comparison
- compliance monitoring
- negotiation assistance
- workflow automation

## MVP Definition of Done

A user can:

1. Upload a contract.
2. Process it.
3. Search it semantically.
4. Ask questions.
5. Receive grounded answers.
6. See source evidence.
7. Extract entities.
8. Identify major clauses.
9. See basic potential risk flags.

The MVP must be reliable before advanced features are added.