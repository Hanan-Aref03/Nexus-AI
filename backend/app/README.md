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

## Alerts Slice

The Phase 4 alert inbox is intentionally read-only in its first PR:

- `app/domains/alerts/` derives alerts from the existing analysis records
- `app/api/v1/alerts.py` exposes the first alert feed endpoint
- no new alert table or migration is required yet
- Slack now flows through a local connector seam, while copilot surfaces through an interactive provider chain in the alerts UI

## Copilot Slice

- `app/domains/copilot/` turns the current tenant's alert state into a grounded question-answer flow
- `app/integrations/copilot/` routes Gemini first, Grok second, and a local fallback last
- guardrails and local evaluation run before answers reach the UI so prompt safety and answer quality stay visible

## FinOps Slice

- `app/domains/finops/` turns the current analysis store into conservative savings and forecasting guidance
- `app/api/v1/finops.py` exposes `/api/v1/finops/insights` as the final workspace lens
- no new storage table or migration is required because the phase derives from existing findings and health scores
