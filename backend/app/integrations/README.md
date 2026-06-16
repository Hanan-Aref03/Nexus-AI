# Integrations

This package holds the external connector seams used by the backend.

## Current Shape

- `slack/` contains the alert delivery seam
- the first implementation stays local and deterministic
- future vendor transports can reuse the same payload contract without changing the alert service

