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

## Phase 2 Highlights

- Deterministic anomaly detection with persisted findings and incidents
- Correlation of related signals into one tenant-scoped incident
- Incident lifecycle updates across `open`, `acknowledged`, `investigating`, and `resolved`
- Service and workload health scores derived from active findings
- Detection endpoints at `POST /api/v1/analysis/run`, `GET /api/v1/analysis/findings`, `GET /api/v1/analysis/incidents`, and `GET /api/v1/analysis/health-scores`

## Phase 4 Highlights

- Read-only alert inbox derived from the existing analysis store
- `/api/v1/alerts` keeps the workspace and Slack delivery seams aligned without a separate alert table yet
- Slack and copilot preview fields are part of the contract so later PRs can wire real integrations cleanly
- No extra migration was needed for this slice because the feed is computed from existing analysis records

## Local Run

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

To run the full repository test suite from the repo root:

```bash
python -m pytest
```

To run the local database + backend stack from the repository root:

```bash
docker compose up --build
```

The root `compose.yml` is the single canonical Docker entrypoint. Database migrations run automatically during application startup so the local environment and the containerized environment stay aligned.
