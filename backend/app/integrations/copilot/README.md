# Copilot Connector Seams

This folder contains the provider chain for the Phase 4 copilot experience.

## Files

- `base.py` defines the shared prompt context and normalized reply
- `prompt.py` builds the grounded prompt and parses structured model replies
- `gemini.py` uses Gemini when a key is configured
- `grok.py` uses xAI Grok as the fallback live provider when configured
- `local.py` keeps the workspace useful when no external provider is available
- `factory.py` creates the provider chain in Gemini -> Grok -> local order

## Intent

- keep the answer grounded in the current tenant evidence
- avoid leaking secrets by redacting questions before provider calls
- keep AI outputs guarded and evaluated before they return to the UI

