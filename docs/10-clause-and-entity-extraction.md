# Clause and Entity Extraction

## Objective

Extract structured information from contract text.

## Entity Types

Initial entities:

- Company
- Person
- Organization
- Date
- Monetary Amount
- Jurisdiction
- Product
- Address

## Clause Types

Initial taxonomy:

- Termination
- Liability
- Indemnification
- Confidentiality
- Payment
- Intellectual Property
- Data Protection
- Non-Compete
- Non-Solicitation
- Renewal
- Governing Law
- Dispute Resolution

## Extraction Strategy

Use a hybrid approach.

### Stage 1

Rule-based and NLP preprocessing.

### Stage 2

LLM structured extraction.

### Stage 3

Validation and normalization.

## Structured Output

Example:

```json
{
  "clause_type": "termination",
  "text": "Either party may terminate...",
  "page": 12,
  "confidence": 0.91
}
```

## Entity Output

```json
{
  "entity_type": "company",
  "name": "Example Corp",
  "normalized_name": "Example Corporation",
  "confidence": 0.94
}
```

## Classification

The initial implementation may use an LLM classifier.

Later, a dedicated classifier can be evaluated.

## Validation

The system should verify:

- extracted text exists in source
- page references are valid
- entity types are valid
- confidence values are valid
- required fields exist

## Important Principle

Do not trust LLM structured output blindly.

Validate the output before storing it.

## Improvement Path

```text
LLM Extraction
      ↓
Evaluation Dataset
      ↓
Error Analysis
      ↓
Better Prompting
      ↓
Optional Fine-Tuned Classifier
```