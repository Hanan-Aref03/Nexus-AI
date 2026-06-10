# NexusAI

AI-native cloud observability and intelligence platform for AWS and Kubernetes operations.

The platform turns telemetry into actionable findings, root-cause analysis, security signals, cost recommendations, and predictive reliability guidance. The brief also uses the name NexusIQ in places; this repository currently treats NexusAI as the working project name.

## Current Focus

Phase 1 is the telemetry foundation:

- FastAPI backend with `GET /health` and `GET /ready`
- OpenTelemetry-first tracing
- Normalized telemetry ingestion
- PostgreSQL storage bootstrap with local dev support
- Adapter seams for future CloudWatch and OpenObserve work
- Modular-monolith backend design so security and tenant policy stay centralized before any split is justified
- Phase 1.5 security and governance hardening is the next planned slice before Phase 2 detection work

## Repo Shape

- `backend/` - FastAPI service, ingestion, analysis, and integrations
- `frontend/` - Next.js dashboard and investigation experience
- `infra/` - Docker, deployment, and infrastructure definitions
- `docs/phases/` - Explanation docs for each roadmap phase
- `docs/adr/` - Architecture decision records and system-level rationale
- `tests/` - Canonical unit, integration, and e2e test harnesses
- `.planning/` - Project memory, requirements, roadmap, and state

## Working Agreement

- Keep implementation work in small, reviewable PRs.
- Prefer vertical slices over large horizontal layers.
- Make each phase buildable, testable, and easy to explain.
- Prefer free/local dependencies first, then layer in live connectors behind adapter seams.
- Treat the backend as a modular monolith until security, auth, and tenant boundaries prove they need to split.

## Local Development

1. Copy `.env.example` to `.env` if you want to run the backend directly on your machine.
2. Start the PostgreSQL and backend stack with `docker compose -f infra/docker/docker-compose.yml up --build`.
3. Run `pytest` from the repo root to exercise the backend normalization and smoke tests.
4. Use the sample batch in `backend/app/domains/telemetry/sample_data.py` for offline demos.
5. Alembic migrations apply automatically during backend startup, so the schema version is always driven from one source of truth.

## Phase Docs

- [Phase 1 - Telemetry Foundation](docs/phases/phase-1-telemetry-foundation.md)
- [Phase 2 - Detection Core](docs/phases/phase-2-detection-core.md)
- [Phase 3 - Investigation UX](docs/phases/phase-3-investigation-ux.md)
- [Phase 4 - Alerts and Copilot](docs/phases/phase-4-alerts-and-copilot.md)
- [Phase 5 - FinOps and Predictive Reliability](docs/phases/phase-5-finops-and-predictive-reliability.md)
