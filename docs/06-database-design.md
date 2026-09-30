# Database Design

## Database Architecture

The system uses:

```text
PostgreSQL
    +
pgvector
    +
Neo4j
```

## PostgreSQL Responsibilities

PostgreSQL stores application and structured data.

## Core Tables

### users

```text
id
email
password_hash/auth_provider_id
created_at
```

### contracts

```text
id
name
contract_type
status
file_path
uploaded_by
created_at
updated_at
```

### documents

```text
id
contract_id
file_name
file_type
page_count
processing_status
error_message
created_at
```

### clauses

```text
id
contract_id
document_id
clause_type
text
page_number
confidence
created_at
```

### entities

```text
id
contract_id
entity_type
name
normalized_name
confidence
created_at
```

### obligations

```text
id
contract_id
description
party
deadline
confidence
```

### risk_flags

```text
id
contract_id
clause_id
risk_type
severity
description
evidence
confidence
created_at
```

### chunks

```text
id
document_id
chunk_index
text
page_start
page_end
metadata
embedding
created_at
```

## Vector Storage

Store embeddings using pgvector.

Each vector should retain metadata linking it to:

- document
- contract
- page
- chunk
- clause where applicable

## Metadata Filtering

Semantic retrieval should support filters such as:

- contract ID
- contract type
- date
- entity
- clause type

## Neo4j

Neo4j stores graph relationships.

Example:

```text
(Company)-[:SIGNED]->(Contract)
(Contract)-[:CONTAINS]->(Clause)
(Contract)-[:INVOLVES]->(Person)
(Contract)-[:HAS_OBLIGATION]->(Obligation)
(Contract)-[:GOVERNED_BY]->(Jurisdiction)
(Contract)-[:HAS_RISK]->(Risk)
```

## Database Rules

1. Avoid duplicating data unnecessarily.
2. Use foreign keys where appropriate.
3. Index frequently queried fields.
4. Use migrations.
5. Never hard-code production credentials.
6. Keep vector metadata synchronized with source documents.

## Data Integrity

Deleting a contract must define what happens to:

- chunks
- clauses
- entities
- risks
- graph nodes
- embeddings

The deletion strategy must be explicit.