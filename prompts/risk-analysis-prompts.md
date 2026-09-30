# Risk Analysis Prompts

## Purpose

Define prompts used to identify potential contractual risks.

## Important Safety Rule

The model must not provide definitive legal conclusions.

It must identify **potential issues requiring human review**.

## Input

The model receives:

- clause text
- clause type
- contract metadata
- relevant context

## Output

```json
{
  "risk_detected": true,
  "risk_type": "automatic_renewal",
  "severity": "MEDIUM",
  "confidence": 0.88,
  "explanation": "...",
  "evidence": "..."
}
```

## Rules

The model must:

- use only supplied evidence
- avoid inventing facts
- quote or reference evidence
- distinguish potential risk from legal certainty
- identify uncertainty
- avoid legal advice

## Risk Categories

- Liability
- Indemnification
- Termination
- Renewal
- Confidentiality
- Intellectual Property
- Data Protection
- Compliance
- Payment
- Other

## Human Review

Every significant risk should be presented with:

- category
- severity
- explanation
- evidence
- source location

## Evaluation

Measure:

- precision
- recall
- false-positive rate
- false-negative rate

Prompt changes must be evaluated before deployment.