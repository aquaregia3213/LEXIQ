# Security and Privacy

## Why Security Matters

Contracts may contain confidential business information.

Security must therefore be considered from the beginning.

## File Security

Uploaded files must be:

- validated
- size-limited
- type-checked
- safely stored

Do not execute uploaded files.

## Authentication

For MVP, authentication can initially be simplified if the application is local.

Before public deployment, implement proper authentication.

## Authorization

Users must only access contracts they are authorized to access.

## Secrets

Never commit:

- API keys
- database passwords
- tokens
- private credentials

Use environment variables.

## LLM Privacy

Before sending contract content to an external LLM provider, understand:

- data retention
- training policies
- API privacy
- regional processing

Provide a local/open-source model option where practical.

## Prompt Injection

Contract documents are untrusted input.

A malicious document could contain text attempting to manipulate the LLM.

The system must treat contract content as **data**, not instructions.

## Data Isolation

Separate users' contract repositories.

## Logging

Do not log sensitive contract text unnecessarily.

Prefer logging:

- document ID
- operation
- status
- error type
- latency

## Deletion

Deleting a contract should remove or invalidate:

- original file
- extracted data
- embeddings
- graph nodes
- risk results

## Security Principle

Assume uploaded documents are untrusted.

## Legal Disclaimer

The system is not a legal advice system.

AI results must be reviewed by qualified professionals.