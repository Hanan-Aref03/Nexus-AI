# Backend

FastAPI service for telemetry ingestion, analysis, incident handling, and external integrations.

## Intended Internal Shape

- `app/api/` - HTTP routes and API versioning
- `app/core/` - configuration, logging, security, and shared plumbing
- `app/domains/` - telemetry, incidents, intelligence, security, and FinOps domain logic
- `app/integrations/` - AWS, OpenObserve, Slack, and future external connectors
- `app/workers/` - background jobs, pipelines, and scheduled processing
- `tests/` - backend unit and integration tests

The first implementation PR should establish the service entry point, configuration, and one end-to-end telemetry path before more domain modules are added.
