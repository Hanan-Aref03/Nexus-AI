# Phase 1.5 - Security and Governance Baseline

## Why This Phase Exists

The telemetry foundation is only safe if the platform can protect secrets, enforce tenant boundaries, redact sensitive data, and constrain AI-facing surfaces before the detection core and copilot work begin.

This phase is the hardening layer between the telemetry foundation and the detection engine.

## What Ships in This Phase

- Vault-backed secret management with a local-development-friendly fallback
- Explicit CORS policy and async-first request/data paths
- Authentication and authorization for protected endpoints
- PostgreSQL row-level security for tenant isolation
- Trace, log, and prompt redaction at the application boundary
- Security/audit events emitted in a SIEM-friendly shape
- NeMo Guardrails around any LLM-facing path
- RAGAS evaluation for generated outputs and prompt changes
- A documented modular-monolith decision in [ADR 0001](../adr/0001-modular-monolith.md) so the backend stays coherent while the product is still taking shape
- The first PR in this phase implements the request and data-plane security foundation: CORS, signed bearer auth, tenant-scoped telemetry, redaction, Vault secret loading, and the guardrail/evaluation seams

## Why We Keep the Backend as a Modular Monolith

The first release needs one secure deployment path, one migration chain, and one place to enforce identity and data policy.

That makes a modular monolith the right choice for now because:

1. Security policy is easier to enforce when auth, redaction, and RLS all live in one backend.
2. Operational overhead stays low while the product is still proving the shape of its domains.
3. Observability is simpler when one process emits the core traces and audit events.
4. Domain boundaries can still be strict without splitting into separate deployable services too early.

## What Is Deferred

- Detection core anomaly scoring and incident correlation
- Investigation dashboards and service graphs
- Slack alerts and copilot workflows
- FinOps optimization and predictive reliability

## Delivery Shape

This phase should still ship in small PRs. The clean sequence is:

1. Secrets, CORS, and trace redaction
2. AuthN/AuthZ and PostgreSQL RLS
3. Guardrails and RAGAS evaluation hooks

That keeps the platform secure without turning the hardening work into one oversized PR.
