# Requirements: NexusAI

**Defined:** 2026-06-09
**Core Value:** Convert raw cloud telemetry into evidence-backed actions faster than a human team can correlate dashboards, alerts, and logs by hand.

## v1 Requirements

Requirements for the first release. Each maps to roadmap phases.

### Ingestion

- [ ] **ING-01**: User can connect an AWS CloudWatch source.
- [ ] **ING-02**: User can connect an OpenObserve source.
- [ ] **ING-03**: System ingests logs, metrics, traces, alerts, and Kubernetes events into normalized storage.
- [ ] **ING-04**: System associates telemetry with services, clusters, and workloads.

### Analysis

- [ ] **ANLY-01**: System detects telemetry anomalies and creates findings.
- [ ] **ANLY-02**: System correlates related signals into a single incident.
- [ ] **ANLY-03**: System generates root-cause analysis with probable cause, confidence, evidence, and remediation recommendations.
- [ ] **ANLY-04**: System provides a service or workload health score.
- [ ] **ANLY-05**: System identifies security anomalies such as unusual authentication attempts, suspicious API activity, privilege escalation, or abnormal traffic spikes.
- [ ] **ANLY-06**: System identifies overprovisioned or idle resources and estimates monthly savings.
- [ ] **ANLY-07**: System forecasts storage exhaustion, resource saturation, traffic growth, or service degradation.

### Experience

- [ ] **EXP-01**: User can browse findings in a web dashboard.
- [ ] **EXP-02**: User can open an incident detail view showing timeline, evidence, and current status.
- [ ] **EXP-03**: User can navigate a service dependency graph or relationship map.
- [ ] **EXP-04**: User can ask the AI copilot questions about incidents, costs, or service health.
- [ ] **EXP-05**: User can view or generate an incident postmortem summary.

### Operations

- [ ] **OPS-01**: User can receive Slack alerts for important findings or incident updates.
- [ ] **OPS-02**: User can move incidents through open, acknowledged, investigating, and resolved states.

### Platform and Security

- [ ] **SEC-01**: Secrets are stored in Vault or a Vault-compatible local secret store and never hardcoded in the repository.
- [ ] **SEC-02**: Traces, logs, and prompt payloads are redacted before export so sensitive data does not leave the app in plaintext.
- [ ] **SEC-03**: The backend enforces an explicit CORS policy and rejects unexpected origins.
- [ ] **SEC-04**: Users authenticate and authorize through tenant-aware claims before they can access protected resources.
- [ ] **SEC-05**: PostgreSQL row-level security prevents cross-tenant data access.
- [ ] **SEC-06**: Security and audit events are emitted in a SIEM-friendly format for later review and detection workflows.
- [ ] **SEC-07**: AI-facing features are constrained by NeMo Guardrails or equivalent policy guardrails.
- [ ] **SEC-08**: AI outputs are evaluated with RAGAS before they are released to users.
- [ ] **SEC-09**: Backend request handlers and persistence paths remain async-first for IO-bound work.

### Architecture

- [ ] **ARC-01**: The backend remains a modular monolith with explicit domain boundaries until a split is justified by measurable scale or ownership pressure.

## v2 Requirements

Deferred to future release. Tracked so they do not quietly creep into v1.

### Enterprise

- **ENT-01**: Cross-tenant intelligence that learns from multiple customers.
- **ENT-02**: SSO and audit logs.
- **ENT-03**: Usage-based billing and plan management.

### Model Strategy

- **ML-01**: Hybrid routing between local models and frontier models for deeper investigations.

## Out of Scope

Explicitly excluded from the first release.

| Feature | Reason |
|---------|--------|
| Automated remediation actions | Recommendations first; execution adds too much risk for the MVP. |
| Broad multi-cloud support beyond AWS/Kubernetes/OpenTelemetry | The MVP stays focused on the stack named in the brief. |
| Mobile app | The product is designed as a web-first operations console. |

## Traceability

Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ING-01 | Phase 1 | Pending |
| ING-02 | Phase 1 | Pending |
| ING-03 | Phase 1 | Pending |
| ING-04 | Phase 1 | Pending |
| SEC-01 | Phase 1.5 | Pending |
| SEC-02 | Phase 1.5 | Pending |
| SEC-03 | Phase 1.5 | Pending |
| SEC-04 | Phase 1.5 | Pending |
| SEC-05 | Phase 1.5 | Pending |
| SEC-06 | Phase 1.5 | Pending |
| SEC-07 | Phase 1.5 | Pending |
| SEC-08 | Phase 1.5 | Pending |
| SEC-09 | Phase 1.5 | Pending |
| ARC-01 | Phase 1.5 | Pending |
| ANLY-01 | Phase 2 | Pending |
| ANLY-02 | Phase 2 | Pending |
| ANLY-03 | Phase 2 | Pending |
| ANLY-04 | Phase 2 | Pending |
| OPS-02 | Phase 2 | Pending |
| EXP-01 | Phase 3 | Pending |
| EXP-02 | Phase 3 | Pending |
| EXP-03 | Phase 3 | Pending |
| EXP-05 | Phase 3 | Pending |
| OPS-01 | Phase 4 | Pending |
| EXP-04 | Phase 4 | Pending |
| ANLY-05 | Phase 4 | Pending |
| ANLY-06 | Phase 5 | Pending |
| ANLY-07 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0

**Coverage note:**
- Security, architecture, and AI-evaluation requirements are intentionally grouped into Phase 1.5 so they can land as a dedicated hardening slice before Phase 2 starts.

---
*Requirements defined: 2026-06-09*
*Last updated: 2026-06-10 after security and governance planning*
