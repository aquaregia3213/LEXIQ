# Knowledge Graph Design

## Purpose

The knowledge graph represents relationships across the contract repository.

Vector search finds semantically relevant text.

The knowledge graph represents structured relationships.

## Node Types

### Company

Properties:

```text
id
name
normalized_name
```

### Person

Properties:

```text
id
name
```

### Contract

Properties:

```text
id
name
type
date
```

### Clause

Properties:

```text
id
type
text
```

### Obligation

Properties:

```text
id
description
deadline
```

### Jurisdiction

Properties:

```text
name
```

### Risk

Properties:

```text
id
type
severity
```

## Relationships

```text
Company ──SIGNED──> Contract
Contract ──CONTAINS──> Clause
Contract ──INVOLVES──> Person
Contract ──HAS_OBLIGATION──> Obligation
Contract ──GOVERNED_BY──> Jurisdiction
Contract ──HAS_RISK──> Risk
Company ──PARTY_TO──> Contract
```

## Example Query

Find contracts involving a company:

```cypher
MATCH (c:Company {name: "Company X"})-[:PARTY_TO]->(contract:Contract)
RETURN contract
```

## Example Relationship Query

Find contracts containing risky clauses:

```cypher
MATCH (c:Contract)-[:CONTAINS]->(clause:Clause)-[:HAS_RISK]->(risk:Risk)
WHERE risk.severity = "HIGH"
RETURN c, clause, risk
```

## Entity Resolution

Different references to the same company should ideally map to one canonical entity.

Example:

```text
Microsoft Corporation
Microsoft Corp.
Microsoft
```

should be normalized where confidence is sufficient.

## Graph Construction

Graph construction occurs after extraction.

Pipeline:

```text
Document
 ↓
Entity Extraction
 ↓
Entity Normalization
 ↓
Clause Extraction
 ↓
Relationship Detection
 ↓
Neo4j Node Creation
 ↓
Relationship Creation
```

## Graph Usage

Use the graph for:

- relationship exploration
- entity-centric search
- cross-contract analysis
- structured filtering
- multi-hop queries

Do not force every query through the graph.

Use vector retrieval when semantic text retrieval is the better tool.