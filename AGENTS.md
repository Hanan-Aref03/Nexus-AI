<!-- GSD:project-start source:PROJECT.md -->
## Project

**NexusAI**

NexusAI is an AI-native cloud observability and intelligence platform that turns logs, metrics, traces, security events, and infrastructure telemetry into actionable operational guidance. It is optimized for AWS and Kubernetes first, with the initial product focusing on CloudWatch, OpenObserve, OpenTelemetry, Prometheus, EKS, ECS, Lambda, RDS, and Kubernetes events.

The brief uses NexusAI and NexusIQ interchangeably. For now, treat NexusAI as the working project name and keep the branding decision open until the product identity is finalized.

**Core Value:** Convert raw cloud telemetry into evidence-backed actions faster than a human team can correlate dashboards, alerts, and logs by hand.

### Constraints

- **Tech stack**: FastAPI backend, PostgreSQL with pgvector, Next.js frontend, Dockerized local development - these are called out directly in the brief.
- **Scope**: Vertical MVP first - each phase should deliver a usable end-to-end slice instead of only a technical layer.
- **Platform focus**: AWS, Kubernetes, and OpenTelemetry first - broader cloud coverage comes later.
- **Delivery style**: Small PRs only - keep changes easy to review and avoid mixing unrelated concerns.
- **Timeline**: The brief targets a fast MVP, so early decisions must optimize for momentum and learning rather than completeness.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
