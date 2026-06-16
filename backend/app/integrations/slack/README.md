# Slack Connector Seam

This folder contains the alert delivery boundary for Phase 4.

## Files

- `base.py` defines the structured payload and connector contract
- `local.py` formats a deterministic preview without calling Slack
- `factory.py` creates the connector used by the FastAPI app

## Intent

- keep the first PR free of vendor credentials
- preserve one stable delivery contract for later live transports
- make the alert service call a connector instead of hard-coding message formatting

