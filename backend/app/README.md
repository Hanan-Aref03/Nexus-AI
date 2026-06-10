# Backend App

This directory holds the FastAPI application package.

The planned decomposition is intentionally domain-oriented:

- `api/` for request and response surfaces
- `core/` for shared runtime concerns
- `domains/` for bounded contexts like telemetry, analysis, incidents, security, and FinOps
- `integrations/` for AWS, OpenObserve, Slack, and other connector seams
- `workers/` for async processing and scheduled jobs

Inside each domain, keep one clear home for each concern:

- `adapters/` for source or provider normalization
- `models.py` for ORM entities
- `repositories/` for persistence logic
- `services/` for orchestration and use cases
- `schemas.py` for request and response contracts

Keep new modules narrow and purposeful so each implementation PR stays easy to review.
