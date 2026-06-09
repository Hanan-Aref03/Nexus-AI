# Backend App

This directory will hold the FastAPI application package.

The planned decomposition is intentionally domain-oriented:

- `api/` for request/response surfaces
- `core/` for shared runtime concerns
- `domains/` for telemetry, analysis, incidents, security, and FinOps
- `integrations/` for AWS/OpenObserve/Slack connectors
- `workers/` for async processing and scheduled jobs

Keep new modules narrow and purposeful so each implementation PR stays easy to review.
