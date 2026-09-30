# Classification Prompts

## Purpose

Define prompts used for clause classification.

## Clause Categories

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
- Other

## Classification Rules

The model must:

1. Select only from the predefined categories.
2. Use the supplied clause text.
3. Avoid unsupported assumptions.
4. Return confidence.
5. Explain classification briefly where useful.

## Output

```json
{
  "category": "Termination",
  "confidence": 0.93,
  "reason": "The clause describes conditions under which either party may terminate the agreement."
}
```

## Evaluation

Every prompt version must be evaluated against manually labeled examples.

## Improvement

Use error analysis to identify:

- confusing categories
- ambiguous clauses
- false classifications
- missing categories

Do not add categories merely because one example is difficult.