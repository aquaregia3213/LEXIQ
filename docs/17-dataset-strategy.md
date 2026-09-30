# Dataset Strategy

## Objective

Create a legal-document dataset that can be used for:

- development
- testing
- evaluation
- extraction
- classification
- RAG evaluation
- risk detection

## Data Sources

Prefer:

1. Publicly available contracts
2. Open legal datasets
3. Synthetic contracts
4. Permissively licensed documents

Always verify licensing before redistribution.

## Synthetic Data

Synthetic contracts can be generated to test controlled scenarios.

Examples:

- automatic renewal
- unlimited liability
- indemnification
- termination
- confidentiality
- IP assignment

Synthetic data should not be presented as real legal documents.

## Annotation

Create labels for:

- entities
- clause types
- risks
- relationships

## Evaluation Dataset

Maintain a manually verified dataset separate from development data.

## Example Question Dataset

```text
Question:
Which contracts contain automatic renewal?

Expected contracts:
contract_01
contract_07

Expected evidence:
contract_01 page 12
contract_07 page 8
```

## Ground Truth

Ground truth should be created or reviewed manually.

Do not use an LLM's answer as unquestioned ground truth.

## Data Privacy

Do not upload confidential real-world contracts to external services without appropriate authorization.

## Dataset Versioning

Track:

- dataset version
- source
- license
- labels
- annotation date
- changes