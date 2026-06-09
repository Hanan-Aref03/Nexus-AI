# NexusAI

AI-native cloud observability and intelligence platform for AWS and Kubernetes operations.

The product turns telemetry into actionable findings, root-cause analysis, security signals, cost recommendations, and predictive reliability guidance. The brief also uses the name NexusIQ in places; this repository currently treats NexusAI as the working project name.

## Repo Shape

- `backend/` - FastAPI service, ingestion, analysis, and integrations
- `frontend/` - Next.js dashboard and investigation experience
- `infra/` - Docker, deployment, and infrastructure definitions
- `docs/` - Architecture notes, runbooks, and decision records
- `tests/` - End-to-end and regression test harnesses
- `.planning/` - Project memory, requirements, roadmap, and state

## Working Agreement

- Keep implementation work in small, reviewable PRs.
- Prefer vertical slices over large horizontal layers.
- Make each phase buildable, testable, and easy to explain.

## First Build Direction

1. Foundation: repo structure, Docker, PostgreSQL, FastAPI, and Next.js entry points.
2. Ingestion: CloudWatch and OpenObserve connectors plus normalized telemetry storage.
3. Intelligence: anomaly detection, RCA, incident correlation, and health scoring.
4. Experience: dashboard, incident views, copilot, alerts, and operational summaries.

