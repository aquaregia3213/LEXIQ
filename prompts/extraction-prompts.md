# Extraction Prompts

## Purpose

Centralize prompts used for structured information extraction.

Prompts must be versioned.

## Entity Extraction Prompt

The model should:

- extract only entities supported by the schema
- preserve source text
- avoid inventing entities
- return structured JSON
- include confidence
- identify source location when possible

## Clause Extraction Prompt

The model should:

- identify clauses
- classify them
- preserve original clause text
- provide source location
- avoid inventing missing clauses

## Extraction Rules

1. Never invent source text.
2. Never create entities that are not supported by evidence.
3. Preserve original wording.
4. Return structured output.
5. Mark uncertainty.
6. Validate output before storage.

## Prompt Versioning

Use:

```text
extraction_v1
extraction_v2
```

When changing prompts, evaluate the new version against the evaluation dataset.

## Example Structured Schema

```json
{
  "items": [
    {
      "type": "company",
      "name": "Example Corp",
      "source_text": "Example Corp",
      "confidence": 0.95
    }
  ]
}
```