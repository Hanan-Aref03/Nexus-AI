# Backend

FastAPI service for telemetry ingestion, analysis, incident handling, and external integrations.

## Intended Internal Shape

- `app/api/` - HTTP routes and API versioning
- `app/core/` - configuration, database access, telemetry bootstrap, and shared plumbing
- `app/domains/` - telemetry, incidents, intelligence, security, and FinOps domain logic
- `app/integrations/` - AWS, OpenObserve, Slack, and future external connectors
- `app/workers/` - background jobs, pipelines, and scheduled processing
- `alembic/` - versioned database migrations
- `tests/` - canonical unit and integration tests live at the repository root
- The backend is intentionally a modular monolith for now so auth, redaction, RLS, and guardrails stay centralized

## PR1 Highlights

- OpenTelemetry SDK bootstrap with a request span middleware
- `GET /health` and `GET /ready`
- Normalized telemetry ingestion at `POST /api/v1/telemetry/ingest`
- Adapter discovery at `GET /api/v1/adapters`
- Recent telemetry inspection at `GET /api/v1/telemetry/signals`
- Alembic-managed schema bootstrap for the telemetry store
- Phase 1.5 adds the first security slice: CORS, signed bearer auth, tenant-scoped telemetry, redaction, Vault seams, and guardrail/evaluation seams

## Local Run

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

The root repository also ships a Docker compose stack under `infra/docker/` for the database + backend path. Database migrations run automatically during application startup so the local environment and the containerized environment stay aligned.
