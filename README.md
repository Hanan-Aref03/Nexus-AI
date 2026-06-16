# NexusAI

AI-native cloud observability and intelligence platform for AWS and Kubernetes operations.

The platform turns telemetry into actionable findings, root-cause analysis, security signals, cost recommendations, and predictive reliability guidance. The brief also uses the name NexusIQ in places; this repository currently treats NexusAI as the working project name.

## Current Focus

The workspace now spans the full path from telemetry foundation to the final FinOps slice:

- FastAPI backend with `GET /health` and `GET /ready`
- OpenTelemetry-first tracing
- Normalized telemetry ingestion
- PostgreSQL storage bootstrap with local dev support
- Adapter seams for future CloudWatch and OpenObserve work
- Modular-monolith backend design so security and tenant policy stay centralized before any split is justified
- Phase 1.5 security and governance hardening is underway with CORS, signed bearer auth, tenant-scoped persistence, redaction, Vault seams, and guardrail/evaluation seams
- Phase 5 is finalizing the workspace with FinOps and predictive reliability insights derived from the existing analysis store

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
2. Start the full local stack with `.\scripts\nexusai.ps1` from the repository root. This is the preferred one-command runner and launches PostgreSQL, the FastAPI backend, and the frontend through Docker Compose.
3. Run `.\scripts\nexusai.ps1 check` to execute the validation bundle: backend tests, frontend typecheck, and Docker Compose config validation.
4. Use `.\scripts\nexusai.ps1 logs` to stream combined service logs, and `.\scripts\nexusai.ps1 down` to stop the stack cleanly.
5. If you prefer the raw Docker command, `docker compose up --build` still works from the repository root.
6. Use the sample batch in `backend/app/domains/telemetry/sample_data.py` for offline demos.
7. Alembic migrations apply automatically during backend startup, so the schema version is always driven from one source of truth.
8. Open `http://localhost:3000` to explore the frontend dashboard once the stack is running.

## Phase Docs

- [Phase 1 - Telemetry Foundation](docs/phases/phase-1-telemetry-foundation.md)
- [Phase 2 - Detection Core](docs/phases/phase-2-detection-core.md)
- [Phase 3 - Investigation UX](docs/phases/phase-3-investigation-ux.md)
- [Phase 4 - Alerts and Copilot](docs/phases/phase-4-alerts-and-copilot.md)
- [Phase 5 - FinOps and Predictive Reliability](docs/phases/phase-5-finops-and-predictive-reliability.md)
