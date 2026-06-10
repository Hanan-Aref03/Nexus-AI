# Roadmap: NexusAI

This roadmap is intentionally vertical and PR-sized. Each phase should produce a reviewable slice that can ship independently without mixing unrelated concerns.

## Phase 1: Telemetry Foundation

**Goal:** Stand up the repo, runtime, storage, and first source integrations so telemetry can enter the system end to end.
**Mode:** mvp

**Requirements Covered:**
- ING-01
- ING-02
- ING-03
- ING-04

**Success Criteria**
1. A local developer can start the platform with Docker-backed services and reach the API and database.
2. CloudWatch and OpenObserve adapters can ingest sample telemetry through a common normalized model.
3. Stored telemetry can be associated with services, clusters, and workloads.
4. The first phase leaves behind a clean scaffold for backend, frontend, infra, docs, and tests.

## Phase 1.5: Security and Governance Baseline

**Goal:** Harden the modular monolith with secrets management, identity, tenant isolation, redaction, and AI guardrails before the detection engine begins to consume more data.
**Mode:** mvp

**Requirements Covered:**
- SEC-01
- SEC-02
- SEC-03
- SEC-04
- SEC-05
- SEC-06
- SEC-07
- SEC-08
- SEC-09
- ARC-01

**Success Criteria**
1. Secrets are sourced from Vault or a Vault-compatible local path, with no secret values committed to the repo or hardcoded in environment examples.
2. Requests are protected by explicit CORS policy, authentication, and authorization, with tenant-scoped access enforced through PostgreSQL row-level security.
3. Traces, logs, and prompt payloads are redacted at the boundary so sensitive data does not leave the app in plaintext.
4. AI-facing features have guardrails and evaluation gates using NeMo Guardrails and RAGAS before they can ship.
5. Security and audit events are emitted in a SIEM-friendly format for later detection and review.
6. The backend remains a modular monolith with async-first IO boundaries and domain modules that can be split later only if evidence justifies it.

## Phase 2: Detection Core

**Goal:** Convert normalized telemetry into findings, incidents, RCA, and health signals.
**Mode:** mvp

**Requirements Covered:**
- ANLY-01
- ANLY-02
- ANLY-03
- ANLY-04
- OPS-02

**Success Criteria**
1. Telemetry anomalies produce actionable findings instead of raw noise.
2. Related findings collapse into a single incident with a lifecycle state.
3. Incident output includes probable cause, confidence, evidence, and remediation guidance.
4. Service or workload health scores are exposed through the backend surface.

## Phase 3: Investigation UX

**Goal:** Give users a dashboard to inspect findings, incidents, dependency graphs, and postmortem summaries.
**Mode:** mvp

**Requirements Covered:**
- EXP-01
- EXP-02
- EXP-03
- EXP-05

**Success Criteria**
1. The dashboard shows current findings in a readable operational view.
2. Incident detail pages show timeline, evidence, and current status clearly.
3. A service dependency graph or relationship map helps explain blast radius and dependencies.
4. Postmortem summaries can be generated or viewed from the incident workflow.

## Phase 4: Alerts and Copilot

**Goal:** Help teams react faster with Slack notifications, AI Q&A, and security anomaly surfacing.
**Mode:** mvp

**Requirements Covered:**
- OPS-01
- EXP-04
- ANLY-05

**Success Criteria**
1. Important findings and incident updates can be pushed to Slack.
2. The AI copilot can answer questions about incidents, costs, and service health.
3. Security anomaly fiprepare this as the first small PR branch for Phase 1ndings appear in the same operational flow as other findings.

## Phase 5: FinOps and Predictive Reliability

**Goal:** Add cost and reliability foresight so the platform recommends what to fix before trouble becomes visible.
**Mode:** mvp

**Requirements Covered:**
- ANLY-06
- ANLY-07

**Success Criteria**
1. Overprovisioned or idle resources surface with estimated monthly savings.
2. The system forecasts storage exhaustion, resource saturation, traffic growth, or degradation.
3. Predictive insights are understandable enough to drive action, not just curiosity.

## Phase Details

**Phase 1: Telemetry Foundation**
Goal: Stand up the repo, runtime, storage, and first source integrations so telemetry can enter the system end to end.
Requirements: ING-01, ING-02, ING-03, ING-04
Success criteria:
1. A local developer can start the platform with Docker-backed services and reach the API and database.
2. CloudWatch and OpenObserve adapters can ingest sample telemetry through a common normalized model.
3. Stored telemetry can be associated with services, clusters, and workloads.
4. The first phase leaves behind a clean scaffold for backend, frontend, infra, docs, and tests.

**Phase 1.5: Security and Governance Baseline**
Goal: Harden the modular monolith with secrets management, identity, tenant isolation, redaction, and AI guardrails before the detection engine begins to consume more data.
Requirements: SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, SEC-06, SEC-07, SEC-08, SEC-09, ARC-01
Success criteria:
1. Secrets are sourced from Vault or a Vault-compatible local path, with no secret values committed to the repo or hardcoded in environment examples.
2. Requests are protected by explicit CORS policy, authentication, and authorization, with tenant-scoped access enforced through PostgreSQL row-level security.
3. Traces, logs, and prompt payloads are redacted at the boundary so sensitive data does not leave the app in plaintext.
4. AI-facing features have guardrails and evaluation gates using NeMo Guardrails and RAGAS before they can ship.
5. Security and audit events are emitted in a SIEM-friendly format for later detection and review.
6. The backend remains a modular monolith with async-first IO boundaries and domain modules that can be split later only if evidence justifies it.

**Phase 2: Detection Core**
Goal: Convert normalized telemetry into findings, incidents, RCA, and health signals.
Requirements: ANLY-01, ANLY-02, ANLY-03, ANLY-04, OPS-02
Success criteria:
1. Telemetry anomalies produce actionable findings instead of raw noise.
2. Related findings collapse into a single incident with a lifecycle state.
3. Incident output includes probable cause, confidence, evidence, and remediation guidance.
4. Service or workload health scores are exposed through the backend surface.

**Phase 3: Investigation UX**
Goal: Give users a dashboard to inspect findings, incidents, dependency graphs, and postmortem summaries.
Requirements: EXP-01, EXP-02, EXP-03, EXP-05
Success criteria:
1. The dashboard shows current findings in a readable operational view.
2. Incident detail pages show timeline, evidence, and current status clearly.
3. A service dependency graph or relationship map helps explain blast radius and dependencies.
4. Postmortem summaries can be generated or viewed from the incident workflow.

**Phase 4: Alerts and Copilot**
Goal: Help teams react faster with Slack notifications, AI Q&A, and security anomaly surfacing.
Requirements: OPS-01, EXP-04, ANLY-05
Success criteria:
1. Important findings and incident updates can be pushed to Slack.
2. The AI copilot can answer questions about incidents, costs, and service health.
3. Security anomaly findings appear in the same operational flow as other findings.

**Phase 5: FinOps and Predictive Reliability**
Goal: Add cost and reliability foresight so the platform recommends what to fix before trouble becomes visible.
Requirements: ANLY-06, ANLY-07
Success criteria:
1. Overprovisioned or idle resources surface with estimated monthly savings.
2. The system forecasts storage exhaustion, resource saturation, traffic growth, or degradation.
3. Predictive insights are understandable enough to drive action, not just curiosity.
