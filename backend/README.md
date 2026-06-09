# Backend

FastAPI service for telemetry ingestion, analysis, incident handling, and external integrations.

## Intended Internal Shape

- `app/api/` - HTTP routes and API versioning
- `app/core/` - configuration, database access, telemetry bootstrap, and shared plumbing
- `app/domains/` - telemetry, incidents, intelligence, security, and FinOps domain logic
- `app/integrations/` - AWS, OpenObserve, Slack, and future external connectors
- `app/workers/` - background jobs, pipelines, and scheduled processing
- `tests/` - backend unit and integration tests

## PR1 Highlights

- OpenTelemetry SDK bootstrap with a request span middleware
- `GET /health` and `GET /ready`
- Normalized telemetry ingestion at `POST /api/v1/telemetry/ingest`
- Adapter discovery at `GET /api/v1/adapters`
- Recent telemetry inspection at `GET /api/v1/telemetry/signals`

## Local Run

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

The root repository also ships a Docker compose stack under `infra/docker/` for the database + backend path.
