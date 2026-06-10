# Telemetry Domain

Telemetry is the first bounded context in the modular monolith, so the package
is organized around one clear rule: keep each concern in one obvious place.

## Layout

- `adapters/` for source-specific normalization and future connector seams
- `models.py` for ORM entities and shared database metadata
- `repositories/` for persistence and read/write queries
- `services/` for use-case orchestration and business flow
- `schemas.py` for request and response contracts
- `sample_data.py` for deterministic demo payloads used in tests and docs

## Why This Shape

This keeps the backend domain-first instead of mixing unrelated features into a
global `services/` or `repositories/` directory. As the platform grows, each new
domain should follow the same pattern so the codebase stays readable and easy to
extract later if the monolith ever needs to split.
