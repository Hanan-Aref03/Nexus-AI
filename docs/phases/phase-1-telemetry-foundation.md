# Phase 1 - Telemetry Foundation

## Why This Phase Exists

This phase creates the smallest useful platform foundation: a backend that can run locally, accept normalized telemetry, persist it to PostgreSQL, and emit OpenTelemetry spans without relying on paid services.

## What Ships in PR1

- FastAPI service with `GET /health` and `GET /ready`
- OpenTelemetry SDK bootstrap with an explicit request-tracing middleware
- Normalized telemetry intake at `POST /api/v1/telemetry/ingest`
- Adapter discovery at `GET /api/v1/adapters`
- Recent telemetry inspection at `GET /api/v1/telemetry/signals`
- PostgreSQL schema bootstrap plus SQLite-friendly test behavior

## Free and Local by Default

- OpenTelemetry is the primary observability API
- Sample and OTLP-compatible adapters are ready now
- CloudWatch and OpenObserve remain behind the adapter seam and are marked as planned
- No paid SaaS, no paid LLMs, and no external credentials are required for the phase-1 demo path

## How the Data Flows

1. A source batch arrives through the normalized intake contract.
2. The adapter registry selects the correct source adapter.
3. The repository stores the normalized signals in PostgreSQL.
4. The API can then return the stored signals for inspection or smoke testing.

## What Is Deferred

- Root-cause analysis and incident correlation
- Slack notifications
- Copilot chat
- FinOps intelligence
- Predictive reliability scoring
- Cross-tenant intelligence

## Local Run Notes

- Start the database and backend with the Docker stack in `infra/docker/docker-compose.yml`
- Use the sample batch in `app/domains/telemetry/sample_data.py` for local demos and tests
- Treat this phase as the foundation for later operational intelligence work, not as the final product

