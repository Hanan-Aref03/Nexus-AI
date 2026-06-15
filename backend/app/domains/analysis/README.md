# Analysis Domain

This package contains the Phase 2 detection core.

## Layout

- `models.py` for findings, incidents, and signal evaluation records
- `repositories/` for persistence and read queries
- `rules.py` for deterministic anomaly classification and scoring
- `services/` for orchestration and API-facing use cases
- `schemas.py` for request and response contracts

## Design Notes

- Detection is deterministic first, so the local stack can prove the phase
  without paid services or opaque model calls.
- Signals are evaluated once and tracked in an internal ledger so repeated runs
  do not create duplicate findings.
- Findings are grouped into incidents with tenant-aware boundaries and
  row-level security hooks aligned to the rest of the backend.

