# Technology Stack

## Primary Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python + FastAPI | API and application logic |
| Frontend | Next.js + React | User interface |
| Database | PostgreSQL | Structured application data |
| Vector Search | pgvector | Embedding storage/search |
| Knowledge Graph | Neo4j | Relationship mapping |
| NLP | spaCy / Transformers | NLP processing |
| Document Parsing | PyMuPDF / python-docx | PDF/DOCX extraction |
| LLM | Configurable provider | Generation/extraction |
| Embeddings | Configurable embedding model | Semantic search |
| Containerization | Docker | Local environment consistency |

## Python

Use Python for:

- NLP
- document processing
- AI pipelines
- backend services
- evaluation

## FastAPI

Use FastAPI for:

- REST APIs
- document upload
- search
- RAG
- contract endpoints
- risk endpoints

## Next.js

Use Next.js for:

- dashboard
- contract upload
- search interface
- contract viewer
- risk display
- graph visualization
- RAG chat

## PostgreSQL

Use PostgreSQL as the primary relational database.

It should store structured application information.

## pgvector

Use pgvector initially instead of introducing a separate vector database.

Reason:

- simpler architecture
- PostgreSQL integration
- easier deployment
- sufficient for an MVP
- lower infrastructure complexity

A dedicated vector database can be considered later if scale requires it.

## Neo4j

Use Neo4j for:

- entity relationships
- contract relationships
- graph traversal
- relationship exploration

## NLP

Use spaCy and/or Transformers for deterministic or model-based NLP tasks where appropriate.

Use LLMs when flexible semantic extraction is more effective.

## Document Processing

Use:

- PyMuPDF for PDFs
- python-docx for DOCX
- OCR only when necessary

## LLM Architecture

LLM access must be abstracted behind a service interface.

Example conceptual interface:

```python
class LLMService:
    def generate(...)
    def structured_extract(...)
```

The rest of the application should not depend directly on one specific provider.

## Embedding Architecture

Embedding generation should also be abstracted.

The application should support changing embedding models without rewriting retrieval logic.

## Technology Selection Rule

Choose the simplest technology that satisfies the requirement.

Do not introduce:

- Kubernetes
- microservices
- Kafka
- complex agent frameworks
- multiple vector databases

unless a documented requirement justifies them.