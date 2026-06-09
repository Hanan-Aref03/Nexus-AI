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

