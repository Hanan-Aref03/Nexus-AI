# NexusAI

## What This Is

NexusAI is an AI-native cloud observability and intelligence platform that turns logs, metrics, traces, security events, and infrastructure telemetry into actionable operational guidance. It is optimized for AWS and Kubernetes first, with the initial product focusing on CloudWatch, OpenObserve, OpenTelemetry, Prometheus, EKS, ECS, Lambda, RDS, and Kubernetes events.

The brief uses NexusAI and NexusIQ interchangeably. For now, treat NexusAI as the working project name and keep the branding decision open until the product identity is finalized.

## Core Value

Convert raw cloud telemetry into evidence-backed actions faster than a human team can correlate dashboards, alerts, and logs by hand.

## Requirements

### Validated

(None yet - ship to validate)

### Active

- [ ] Ingest telemetry from AWS and OpenObserve sources into a normalized platform model.
- [ ] Detect anomalies, correlate related signals, and generate root-cause analysis with evidence.
- [ ] Surface findings, incidents, health signals, and operational guidance in a web dashboard and copilot.

### Out of Scope

- Cross-tenant intelligence - powerful enterprise differentiator, but it needs volume and governance that do not belong in the MVP.
- Full automated remediation actions - the MVP should recommend actions, not execute them on behalf of users.
- Mobile app - the product is web-first and dashboard-driven for the initial release.

## Context

- Greenfield repository with only the project brief and license present.
- The source brief describes a 2-week MVP shaped around FastAPI, PostgreSQL, pgvector, Next.js, Docker, and AWS/Kubernetes integrations.
- The product is an AI SRE / DevOps / FinOps / Security assistant, not a traditional monitoring dashboard.
- The implementation should stay small, reviewable, and easy to ship in PR-sized slices.

## Constraints

- **Tech stack**: FastAPI backend, PostgreSQL with pgvector, Next.js frontend, Dockerized local development - these are called out directly in the brief.
- **Scope**: Vertical MVP first - each phase should deliver a usable end-to-end slice instead of only a technical layer.
- **Platform focus**: AWS, Kubernetes, and OpenTelemetry first - broader cloud coverage comes later.
- **Delivery style**: Small PRs only - keep changes easy to review and avoid mixing unrelated concerns.
- **Timeline**: The brief targets a fast MVP, so early decisions must optimize for momentum and learning rather than completeness.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use NexusAI as the working project name | It matches the repository name and the brief's primary naming convention | Pending |
| Run the project as a vertical MVP | Best fit for a new product and for small, reviewable PRs | Pending |
| Start with AWS/Kubernetes/OpenTelemetry integrations | This matches the product brief and keeps the first slices realistic | Pending |
| Split the repo around backend, frontend, infra, docs, and tests | Keeps the codebase easy to navigate as the product grows | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-09 after initialization*
