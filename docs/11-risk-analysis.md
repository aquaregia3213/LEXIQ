# Risk Analysis

## Objective

Identify potentially risky or unusual contract provisions.

The system must not provide definitive legal conclusions.

## Initial Risk Categories

### Liability

Examples:

- unlimited liability
- unusually broad liability

### Indemnification

Examples:

- unusually broad indemnification
- one-sided obligations

### Termination

Examples:

- restrictive termination rights
- long notice requirements

### Renewal

Examples:

- automatic renewal
- difficult cancellation

### Compliance

Examples:

- potentially missing data-protection provisions
- unusual compliance obligations

### Intellectual Property

Examples:

- unusually broad IP assignment

## Risk Detection Architecture

Use a hybrid system:

```text
Clause
 ↓
Rule-Based Checks
 ↓
LLM Analysis
 ↓
Evidence Validation
 ↓
Risk Score
 ↓
Human Review
```

## Risk Output

```json
{
  "risk_type": "automatic_renewal",
  "severity": "MEDIUM",
  "confidence": 0.88,
  "description": "...",
  "evidence": "...",
  "page": 14
}
```

## Severity

Use:

- LOW
- MEDIUM
- HIGH

Severity should represent potential importance, not legal certainty.

## Confidence

Confidence should indicate system confidence in the detection.

It must not be presented as probability of legal liability.

## Human Review

Every significant risk should show:

- why it was flagged
- source clause
- page
- risk category
- confidence

## False Positives

False positives are expected.

Evaluation should measure them explicitly.

## Legal Safety

The interface must clearly communicate:

> This is an AI-generated potential risk flag and should be reviewed by a qualified legal professional.

Never present:

> This contract is legally unsafe.

Instead use:

> Potential issue detected: the clause may create unusually broad liability exposure. Review recommended.

## Rule + LLM Strategy

Use deterministic rules for obvious patterns where possible.

Use LLM reasoning for:

- context
- unusual wording
- semantic interpretation

This reduces unnecessary LLM calls and improves consistency.