# FinOps Domain

This domain turns the existing analysis store into the Phase 5 cost and reliability lens.

## Responsibilities

- derive conservative monthly savings estimates from current findings and health scores
- forecast resource saturation, traffic growth, storage pressure, and reliability risk
- keep the implementation computed, explainable, and free/local friendly

## Current Surface

- `service.py` contains the deterministic insight builder
- `schemas.py` defines the API contract returned to the frontend
- `app/api/v1/finops.py` exposes the read-only insights endpoint

## Why This Exists

The final phase should help operators spot waste before it becomes obvious and should do so without requiring a separate billing product, a paid forecasting API, or a new database table.
