# ADR 0001 - Modular Monolith for the Backend

## Status

Accepted for Phase 1 and Phase 1.5.

## Context

NexusAI is starting with a single FastAPI backend, one PostgreSQL database, and one migration chain.

The early product needs to prove telemetry ingestion, security policy, tenant isolation, and AI guardrails before there is enough scale pressure to justify splitting the system into separate deployables.

## Decision

The backend will remain a modular monolith for the initial phases.

The codebase will keep strong domain boundaries inside one deployable service instead of breaking into microservices immediately.

## Why

- One deployable is easier to secure, observe, and operate.
- Authentication, authorization, redaction, and row-level security are simpler to enforce when policy lives in one backend.
- The team can move faster while the domain model is still changing.
- The monolith keeps the local developer experience lightweight and avoids premature distributed-systems complexity.

## Consequences

- Domain modules need clean interfaces so the monolith does not become a tangled codebase.
- Future service extraction should be driven by measurable scale, ownership, or deployment needs.
- Shared infrastructure concerns such as tracing, redaction, and tenant policy stay centralized until there is a strong reason to split them.

## Migration Path

If the product later outgrows the monolith, the extraction path should be domain-based:

1. Preserve the public API contracts.
2. Extract bounded domains one at a time.
3. Keep security policy and tenant rules consistent during the split.
4. Avoid turning the first release into a distributed system before the product earns that complexity.
