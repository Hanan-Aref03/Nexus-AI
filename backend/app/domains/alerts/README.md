# Alerts Domain

This package contains the Phase 4 alert feed.

## Layout

- `repositories/` for reading existing analysis data through a narrow seam
- `rules.py` for turning incidents and health scores into alert drafts
- `services/` for assembling the alert feed returned by the API
- `schemas.py` for request and response contracts

## Design Notes

- The first alerting slice is read-only and computed from the analysis store.
- That keeps the PR small, avoids a new migration, and makes the feed easy to
  test locally with the existing demo telemetry.
- Slack and copilot work are represented as preview fields for now so the
  later integration PRs can swap in real delivery channels without changing the
  feed contract.

