"""Analysis orchestration for the Phase 2 detection core."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from app.core.auth import SecurityPrincipal
from app.domains.analysis.models import AnalysisEvaluationRecord, AnalysisFindingRecord, AnalysisIncidentRecord
from app.domains.analysis.repositories.analysis_repository import AnalysisRepository
from app.domains.analysis.rules import AnalysisFindingDraft, build_finding_draft, build_incident_draft, calculate_health_scores
from app.domains.analysis.schemas import (
    AnalysisEvidenceItem,
    AnalysisFindingOut,
    AnalysisHealthScore,
    AnalysisIncidentOut,
    AnalysisIncidentState,
    AnalysisRunResult,
)


class AnalysisService:
    """Coordinate telemetry evaluation, incident correlation, and reporting."""

    def __init__(self, repository: AnalysisRepository):
        self._repository = repository

    def analyze(self, principal: SecurityPrincipal, limit: int = 200) -> AnalysisRunResult:
        """Evaluate new telemetry signals and persist any resulting findings."""

        signals = self._repository.list_unprocessed_signals(principal, limit=limit)
        finding_groups: dict[str, list[AnalysisFindingDraft]] = defaultdict(list)
        evaluations: list[AnalysisEvaluationRecord] = []
        new_records: list[object] = []

        created_findings = 0
        created_incidents = 0
        updated_incidents = 0
        now = datetime.now(timezone.utc)

        for signal in signals:
            finding_draft = build_finding_draft(signal)
            if finding_draft is None:
                evaluations.append(
                    AnalysisEvaluationRecord(
                        id=str(uuid4()),
                        tenant_id=principal.tenant_id,
                        telemetry_signal_id=signal.id,
                        correlation_key=self._build_fallback_correlation_key(signal),
                        outcome="benign",
                        category=None,
                        reason="Signal did not cross any detection threshold.",
                        evaluated_at=now,
                    )
                )
                continue

            finding_groups[finding_draft.correlation_key].append(finding_draft)
            evaluations.append(
                AnalysisEvaluationRecord(
                    id=str(uuid4()),
                    tenant_id=principal.tenant_id,
                    telemetry_signal_id=finding_draft.telemetry_signal_id,
                    correlation_key=finding_draft.correlation_key,
                    outcome="finding",
                    category=finding_draft.category.value,
                    reason=finding_draft.summary,
                    finding_id=finding_draft.finding_id,
                    evaluated_at=now,
                )
            )

        for correlation_key, drafts in finding_groups.items():
            incident = self._repository.find_active_incident(principal, correlation_key)
            incident_draft = build_incident_draft(drafts)

            if incident is None:
                incident = AnalysisIncidentRecord(
                    id=str(uuid4()),
                    tenant_id=principal.tenant_id,
                    correlation_key=incident_draft.correlation_key,
                    scope_kind=incident_draft.scope_kind.value,
                    scope_name=incident_draft.scope_name,
                    state=AnalysisIncidentState.open.value,
                    title=incident_draft.title,
                    summary=incident_draft.summary,
                    probable_cause=incident_draft.probable_cause,
                    confidence=incident_draft.confidence,
                    evidence_count=len(drafts),
                    finding_count=len(drafts),
                    service_name=incident_draft.service_name,
                    workload_name=incident_draft.workload_name,
                    cluster_name=incident_draft.cluster_name,
                    namespace=incident_draft.namespace,
                    recommendations=incident_draft.recommendations,
                    created_at=now,
                    updated_at=now,
                )
                new_records.append(incident)
                created_incidents += 1
            else:
                incident.summary = self._merge_summary(incident.summary, incident_draft.summary)
                if incident_draft.confidence >= incident.confidence:
                    incident.probable_cause = incident_draft.probable_cause
                incident.confidence = round(max(incident.confidence, incident_draft.confidence), 2)
                incident.evidence_count += len(drafts)
                incident.finding_count += len(drafts)
                incident.recommendations = self._merge_unique_lists(incident.recommendations, incident_draft.recommendations)
                incident.updated_at = now
                updated_incidents += 1

            for draft in drafts:
                finding = AnalysisFindingRecord(
                    id=draft.finding_id,
                    tenant_id=principal.tenant_id,
                    incident_id=incident.id,
                    telemetry_signal_id=draft.telemetry_signal_id,
                    correlation_key=draft.correlation_key,
                    source_name=draft.source_name,
                    source_type=draft.source_type,
                    observed_at=draft.observed_at,
                    batch_label=draft.batch_label,
                    category=draft.category.value,
                    kind=draft.kind,
                    severity=draft.severity,
                    title=draft.title,
                    summary=draft.summary,
                    confidence=draft.confidence,
                    evidence=draft.evidence,
                    recommendations=draft.recommendations,
                    service_name=draft.service_name,
                    workload_name=draft.workload_name,
                    cluster_name=draft.cluster_name,
                    namespace=draft.namespace,
                    created_at=now,
                )
                new_records.append(finding)
                created_findings += 1

        new_records.extend(evaluations)
        self._repository.add_all(new_records)
        self._repository.commit()

        health_scores = self.list_health_scores(principal)
        return AnalysisRunResult(
            processed_signals=len(signals),
            created_findings=created_findings,
            created_incidents=created_incidents,
            updated_incidents=updated_incidents,
            health_scores=health_scores,
        )

    def list_findings(self, principal: SecurityPrincipal, limit: int = 100) -> list[AnalysisFindingOut]:
        """Return recent findings as API-ready payloads."""

        return [AnalysisFindingOut.model_validate(record) for record in self._repository.list_findings(principal, limit=limit)]

    def list_incidents(self, principal: SecurityPrincipal, limit: int = 50) -> list[AnalysisIncidentOut]:
        """Return recent incidents with their evidence payloads attached."""

        incidents = self._repository.list_incidents(principal, limit=limit)
        return [self._incident_out(principal, incident) for incident in incidents]

    def get_incident(self, principal: SecurityPrincipal, incident_id: str) -> AnalysisIncidentOut | None:
        """Return one incident with its evidence payloads attached."""

        incident = self._repository.get_incident(principal, incident_id)
        if incident is None:
            return None
        return self._incident_out(principal, incident)

    def update_incident_state(
        self,
        principal: SecurityPrincipal,
        incident_id: str,
        state: AnalysisIncidentState,
    ) -> AnalysisIncidentOut | None:
        """Move one incident through the supported lifecycle states."""

        incident = self._repository.get_incident(principal, incident_id)
        if incident is None:
            return None

        incident.state = state.value
        incident.updated_at = datetime.now(timezone.utc)
        if state == AnalysisIncidentState.resolved:
            incident.resolved_at = incident.updated_at
        else:
            incident.resolved_at = None

        self._repository.commit()
        return self._incident_out(principal, incident)

    def list_health_scores(self, principal: SecurityPrincipal, limit: int = 100) -> list[AnalysisHealthScore]:
        """Compute service and workload health from the latest analysis state."""

        findings = self._repository.list_findings(principal, limit=limit)
        incidents = self._repository.list_incidents(principal, limit=limit)
        return calculate_health_scores(findings, incidents)

    def _incident_out(self, principal: SecurityPrincipal, incident: AnalysisIncidentRecord) -> AnalysisIncidentOut:
        """Attach incident evidence rows to the response schema."""

        evidence = [
            AnalysisEvidenceItem(
                finding_id=finding.id,
                telemetry_signal_id=finding.telemetry_signal_id,
                title=finding.title,
                summary=finding.summary,
                category=finding.category,
                severity=finding.severity,
                confidence=finding.confidence,
            )
            for finding in self._repository.list_findings_for_incident(principal, incident.id)
        ]
        payload = {
            "id": incident.id,
            "tenant_id": incident.tenant_id,
            "correlation_key": incident.correlation_key,
            "scope_kind": incident.scope_kind,
            "scope_name": incident.scope_name,
            "state": incident.state,
            "title": incident.title,
            "summary": incident.summary,
            "probable_cause": incident.probable_cause,
            "confidence": incident.confidence,
            "evidence_count": incident.evidence_count,
            "finding_count": incident.finding_count,
            "recommendations": incident.recommendations,
            "service_name": incident.service_name,
            "workload_name": incident.workload_name,
            "cluster_name": incident.cluster_name,
            "namespace": incident.namespace,
            "created_at": incident.created_at,
            "updated_at": incident.updated_at,
            "resolved_at": incident.resolved_at,
            "evidence": evidence,
        }
        return AnalysisIncidentOut.model_validate(payload)

    def _merge_summary(self, existing: str, new: str) -> str:
        """Combine summaries while keeping the output compact."""

        if new in existing:
            return existing
        return f"{existing} New evidence: {new}".strip()

    def _merge_unique_lists(self, left: list[str], right: list[str]) -> list[str]:
        """Combine lists without duplicating repeated guidance lines."""

        merged: list[str] = []
        for item in [*left, *right]:
            if item not in merged:
                merged.append(item)
        return merged

    def _build_fallback_correlation_key(self, signal: object) -> str:
        """Build a stable key for benign signals so the evaluation ledger remains searchable."""

        parts = [
            str(getattr(signal, "tenant_id", "")),
            str(getattr(signal, "cluster_name", "") or getattr(signal, "service_name", "") or getattr(signal, "workload_name", "") or getattr(signal, "namespace", "") or getattr(signal, "source_name", "")),
            str(getattr(signal, "batch_label", "") or getattr(signal, "source_name", "")),
        ]
        return "|".join(part for part in parts if part)
