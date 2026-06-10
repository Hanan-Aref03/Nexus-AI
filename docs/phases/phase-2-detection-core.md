# Phase 2 - Detection Core

## Purpose

Turn normalized telemetry into findings, incidents, and explainable operational signals.

## What This Phase Delivers

- Anomaly detection on logs, metrics, traces, and events
- Incident correlation so related symptoms collapse into one operational object
- Root-cause analysis with confidence and evidence
- Service and workload health scoring

## Dependencies

- Phase 1 must already persist normalized telemetry reliably
- The schema needs enough context to link signals to services, clusters, and workloads

## Notes

- Keep the analysis pipeline deterministic enough to test
- Prefer evidence-backed outputs over vague AI summaries
- Preserve the adapter seam so later source expansions do not rewrite the detection layer
- An ML or DL detector can be added later as a pluggable scorer, but the first-phase baseline stays deterministic so the results remain explainable, testable, and easy to operate without labeled data

## Phase 2 Implementation Slice

- `app/domains/analysis/` owns the detection core in the modular monolith.
- `POST /api/v1/analysis/run` evaluates unprocessed telemetry and persists findings, incidents, and the internal evaluation ledger.
- `GET /api/v1/analysis/findings` and `GET /api/v1/analysis/incidents` expose the resulting operational objects.
- `PATCH /api/v1/analysis/incidents/{incident_id}` moves incidents through the Phase 2 lifecycle.
- `GET /api/v1/analysis/health-scores` returns service and workload health scores derived from active findings.

## Local Commands

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

From the repository root:

```bash
python -m pytest
```

To run the Docker stack with PostgreSQL and the backend together:

```bash
docker compose up --build
```
