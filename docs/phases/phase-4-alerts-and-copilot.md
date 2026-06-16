# Phase 4 - Alerts and Copilot

## Purpose

Help teams respond faster once the platform can already explain what happened.

## What This Phase Delivers

- Slack alerts for important findings and incident updates
- AI copilot chat for incident and service questions
- Security anomaly visibility in the same operational flow

## Dependencies

- Phase 2 analysis outputs
- Phase 3 investigation views

## Notes

- Keep notifications actionable and low-noise
- The copilot should explain evidence, not invent it
- Security alerts should reuse the same telemetry and incident model instead of becoming a separate silo

## Implementation Slice

This phase stays intentionally small:

- derive an alert inbox from the existing analysis store
- expose `GET /api/v1/alerts` as the first backend seam
- render a concise workspace alert queue with an interactive copilot studio
- keep Slack behind a local connector seam so the next transport can swap in cleanly
- avoid a new alert table or migration until the inbox semantics are proven useful

## Why This Shape

- Incidents already aggregate evidence, so they are a stronger base than raw findings for the first alert queue
- Health scores add a second signal that catches degradations before they become noisy incident churn
- The feed stays tenant aware and review friendly, which makes it safe to ship before external delivery channels arrive

## Copilot Direction

- The live assistant stays evidence-first and grounded in the tenant's current alerts and analysis state
- The preferred provider order is a free-tier Gemini path first, then Grok as a fallback if needed, with a local fallback last
- That provider choice stays behind a dedicated seam so the UI and alert flow do not depend on one vendor
