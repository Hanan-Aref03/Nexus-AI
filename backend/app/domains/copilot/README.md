# Copilot Domain

This package owns the Phase 4 question-answering slice.

## Shape

- `schemas.py` defines the request and response payloads
- `service.py` assembles evidence and asks the provider chain for an answer

## Intent

- keep the copilot grounded in the current tenant's alert and analysis state
- prefer Gemini first, Grok second, and a local fallback last
- keep guardrails and evaluation in the request path before answers are returned

