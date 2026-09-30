# Evaluation Strategy

## Objective

Measure whether the system actually works rather than judging it by whether the UI looks impressive.

## Extraction Evaluation

Metrics:

- Precision
- Recall
- F1

Evaluate:

- entities
- clauses
- obligations

## Classification Evaluation

Metrics:

- Accuracy
- Precision
- Recall
- F1

Create a manually verified test dataset.

## Retrieval Evaluation

Metrics:

- Recall@K
- Precision@K
- MRR where appropriate

Evaluate whether relevant clauses appear in retrieved results.

## RAG Evaluation

Evaluate:

### Retrieval Relevance

Are retrieved chunks relevant?

### Groundedness

Is the answer supported by retrieved evidence?

### Correctness

Does the answer correctly answer the question?

### Citation Accuracy

Do citations actually support the answer?

### Hallucination

Does the model invent unsupported information?

## Risk Detection

Measure:

- Precision
- Recall
- F1
- False-positive rate

## Latency

Measure:

- document processing time
- search latency
- RAG latency
- extraction latency

## Cost

Track:

- LLM calls
- tokens
- embedding calls
- infrastructure costs

## Evaluation Dataset

Create a small manually verified dataset containing:

- contracts
- entities
- clause labels
- risk labels
- questions
- expected answers
- expected evidence

## Evaluation Principle

Every major AI feature should have measurable quality criteria.

A feature should not be considered production-ready merely because it produces plausible text.