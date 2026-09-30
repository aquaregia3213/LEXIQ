# RAG Pipeline

## Objective

Build a Retrieval-Augmented Generation pipeline that answers questions using contract evidence.

## Pipeline

```text
User Query
    ↓
Query Processing
    ↓
Query Embedding
    ↓
Vector Search
    ↓
Metadata Filtering
    ↓
Optional Graph Search
    ↓
Context Ranking
    ↓
Prompt Construction
    ↓
LLM
    ↓
Grounded Answer
    ↓
Citations
```

## Retrieval

Retrieve relevant chunks using embeddings.

Each result should contain:

- contract
- document
- chunk
- page
- similarity score
- metadata

## Hybrid Retrieval

Use graph retrieval when the question contains relationship-oriented intent.

Example:

> Which contracts involving Company X contain termination clauses?

Potential flow:

```text
Company X
 ↓
Knowledge Graph
 ↓
Relevant Contracts
 ↓
Vector Search
 ↓
Termination Clauses
```

## Context Construction

Do not send the entire contract repository to the LLM.

Construct a focused context from retrieved evidence.

## Prompt Requirements

The RAG prompt must instruct the model to:

- use only supplied evidence
- avoid unsupported claims
- state when evidence is insufficient
- cite sources
- distinguish facts from interpretation

## Hallucination Mitigation

Use:

- source citations
- retrieval thresholds
- context validation
- structured outputs
- refusal when evidence is insufficient

## Example

Question:

> Which contracts have automatic renewal?

Expected answer structure:

```text
Contracts found: 3

1. Contract A
   Renewal clause: ...
   Page: 12

2. Contract B
   Renewal clause: ...
   Page: 8

3. Contract C
   Renewal clause: ...
   Page: 17
```

## RAG Evaluation

Evaluate:

- retrieval relevance
- answer correctness
- groundedness
- citation correctness
- hallucination rate

## RAG Rule

A fluent answer is not automatically a correct answer.

The system must prioritize evidence over confidence.