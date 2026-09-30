# Testing Strategy

## Objective

Ensure the system is reliable at both software and AI levels.

## Unit Tests

Test:

- parsers
- chunking
- validators
- database functions
- graph functions
- retrieval
- risk rules

## Integration Tests

Test:

```text
Upload
 ↓
Parse
 ↓
Store
 ↓
Embed
 ↓
Retrieve
```

## API Tests

Test:

- successful requests
- invalid inputs
- missing resources
- authentication
- errors

## RAG Tests

Test:

- retrieval quality
- groundedness
- citations
- hallucination
- insufficient-context behavior

## Extraction Tests

Test:

- entity accuracy
- clause classification
- malformed LLM outputs
- missing fields

## Knowledge Graph Tests

Test:

- node creation
- relationship creation
- duplicate entities
- graph queries

## Risk Tests

Test:

- known risky clauses
- known safe clauses
- false positives
- false negatives

## End-to-End Test

A complete test should simulate:

```text
Upload Contract
      ↓
Process
      ↓
Extract
      ↓
Index
      ↓
Ask Question
      ↓
Retrieve
      ↓
Generate Answer
      ↓
Display Evidence
```

## Regression Testing

Whenever prompts, models, chunking, or retrieval settings change, rerun the evaluation suite.

AI behavior can change without obvious code changes.

## Testing Principle

A passing API test does not prove that an AI system is correct.

Software correctness and AI quality must be evaluated separately.