# Deployment

## Development Environment

The application should first run locally.

Recommended local services:

- PostgreSQL
- pgvector
- Neo4j
- backend
- frontend

Docker Compose can be used to simplify local setup.

## Environment Variables

Use `.env`.

Example:

```text
DATABASE_URL=
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
LLM_API_KEY=
EMBEDDING_API_KEY=
```

Never commit real secrets.

Provide `.env.example`.

## Production Architecture

```text
User
 ↓
Frontend
 ↓
Backend API
 ↓
Application Services
 ├── PostgreSQL
 ├── pgvector
 ├── Neo4j
 └── LLM Provider
```

## Deployment Requirements

The deployment must support:

- HTTPS
- environment variables
- database connectivity
- file storage
- logging
- error handling

## Docker

Create Dockerfiles for application components where useful.

Use Docker Compose for local development.

## Monitoring

Track:

- API errors
- processing failures
- latency
- LLM usage
- retrieval failures

## Cost Control

Reduce unnecessary LLM calls by:

- caching
- deterministic rules
- batching
- smaller models where appropriate
- avoiding repeated embedding generation

## Production Warning

The student MVP does not need enterprise-scale infrastructure.

Optimize for:

- reliability
- simplicity
- reproducibility
- low cost

before optimizing for massive scale.