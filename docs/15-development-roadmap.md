# Development Roadmap

## Development Strategy

Build from the smallest working system toward the complete platform.

Do not build advanced features before validating the core pipeline.

## Phase 0: Setup

Tasks:

- initialize repository
- configure Python
- configure backend
- configure frontend
- configure PostgreSQL
- configure pgvector
- configure environment variables

Definition of Done:

The application starts locally.

## Phase 1: Document Ingestion

Build:

- upload API
- file validation
- PDF parsing
- DOCX parsing
- document storage

Definition of Done:

A contract can be uploaded and parsed.

## Phase 2: Chunking

Build:

- text cleaning
- section detection
- semantic chunking
- metadata

Definition of Done:

Contract text is split into searchable chunks with source references.

## Phase 3: Embeddings

Build:

- embedding service
- pgvector storage
- similarity search

Definition of Done:

A query returns semantically relevant contract chunks.

## Phase 4: RAG

Build:

- retrieval
- context construction
- LLM generation
- citations

Definition of Done:

A user can ask questions and receive grounded answers.

## Phase 5: Entity Extraction

Build:

- entity extraction
- normalization
- storage

Definition of Done:

Important entities are extracted from contracts.

## Phase 6: Clause Extraction

Build:

- clause detection
- classification
- confidence
- source references

Definition of Done:

Major clause categories can be identified.

## Phase 7: Knowledge Graph

Build:

- Neo4j integration
- nodes
- relationships
- graph queries

Definition of Done:

Relationships between contracts and entities can be explored.

## Phase 8: Risk Analysis

Build:

- rules
- LLM analysis
- severity
- confidence
- evidence

Definition of Done:

Potential risks can be displayed with source evidence.

## Phase 9: Integration

Integrate:

- ingestion
- search
- RAG
- extraction
- graph
- risk analysis

Definition of Done:

The entire workflow works end-to-end.

## Phase 10: Frontend

Build:

- dashboard
- upload page
- contract list
- contract viewer
- search
- AI chat
- risk dashboard
- graph view

## Phase 11: Evaluation

Build:

- evaluation dataset
- metrics
- experiments
- error analysis

## Phase 12: Deployment

Build:

- Docker setup
- production configuration
- deployment
- logging
- monitoring

## Weekly Schedule

Assume:

- 2 hours/day weekdays
- 4 hours/day weekends

Target duration:

10–14 weeks.

Each week must contain:

- learning
- implementation
- testing
- documentation

Do not sacrifice testing entirely to finish features faster.