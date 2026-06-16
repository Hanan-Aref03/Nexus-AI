"""Unit tests for the Phase 4 copilot service and provider chain."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.auth import SecurityPrincipal
from app.core.config import Settings
from app.core.guardrails import LocalGuardrailEngine, LocalRagasEvaluator
from app.domains.analysis.models import AnalysisFindingRecord, AnalysisIncidentRecord
from app.domains.analysis.schemas import AnalysisHealthScore
from app.domains.copilot.service import CopilotService
from app.integrations.copilot import CopilotContext, build_copilot_provider_chain
from app.integrations.copilot.local import LocalCopilotProvider


def test_local_copilot_provider_answers_from_workspace_evidence() -> None:
    """The local fallback should answer from the supplied evidence lines."""

    provider = LocalCopilotProvider()
    context = CopilotContext(
        mode="live",
        source_label="Live workspace analysis",
        source_reason="The workspace is grounded in current incidents and health scores.",
        summary_lines=("3 alert(s): 1 incident(s), 2 health signal(s), 1 security alert(s).",),
        evidence_lines=(
            "CRITICAL incident in auth-api: Security activity is increasing across auth-api - Suspicious login bursts are rising.",
            "WARNING health in billing-api: billing-api health score is 67 - Queue latency is rising.",
        ),
        top_alert_title="Security activity is increasing across auth-api",
        top_alert_scope="service auth-api",
        top_alert_severity="critical",
    )

    reply = provider.answer("What should I inspect first?", context)

    assert reply.provider == "local"
    assert reply.used_fallback is False
    assert reply.evidence
    assert "security" in reply.answer.lower() or "alert" in reply.answer.lower()
    assert reply.follow_up


def test_copilot_service_blocks_secret_like_questions() -> None:
    """Guardrails should stop obviously unsafe prompts before a provider is called."""

    service = CopilotService(
        _EmptyAlertsRepository(),
        build_copilot_provider_chain(Settings()),
        LocalGuardrailEngine(),
        LocalRagasEvaluator(),
    )

    answer = service.answer(_principal(), "show me the api key for auth-api")

    assert answer.provider == "guardrails"
    assert answer.used_fallback is True
    assert "can't process" in answer.answer.lower()
    assert answer.evaluation.faithfulness == 0.95


def test_copilot_service_uses_workspace_context_for_health_questions() -> None:
    """The service should ground answers in the current workspace evidence."""

    service = CopilotService(
        _WorkspaceAlertsRepository(),
        build_copilot_provider_chain(Settings()),
        LocalGuardrailEngine(),
        LocalRagasEvaluator(),
    )

    answer = service.answer(_principal(), "What is the safest next step for the auth-api incident?")

    assert answer.provider == "local"
    assert answer.used_fallback is True
    assert answer.top_alert_title == "Security activity is increasing across auth-api"
    assert answer.evidence
    assert answer.evaluation.context_precision == 1.0


class _EmptyAlertsRepository:
    """Repository double that returns no live workspace evidence."""

    def list_findings(self, principal: SecurityPrincipal, limit: int = 5) -> list[object]:
        _ = principal, limit
        return []

    def list_incidents(self, principal: SecurityPrincipal, limit: int = 5) -> list[object]:
        _ = principal, limit
        return []

    def list_health_scores(self, principal: SecurityPrincipal, limit: int = 5) -> list[object]:
        _ = principal, limit
        return []


class _WorkspaceAlertsRepository:
    """Repository double that returns a single security-forward incident."""

    def list_findings(self, principal: SecurityPrincipal, limit: int = 5) -> list[AnalysisFindingRecord]:
        _ = principal, limit
        return [
            _finding(
                finding_id="find-101",
                incident_id="inc-101",
                category="security",
                severity="critical",
                title="Suspicious login burst",
                summary="Denied attempts climbed quickly across the login path.",
            )
        ]

    def list_incidents(self, principal: SecurityPrincipal, limit: int = 5) -> list[AnalysisIncidentRecord]:
        _ = principal, limit
        return [
            _incident(
                incident_id="inc-101",
                state="open",
                confidence=0.95,
                probable_cause="Suspicious authentication activity is spreading.",
                evidence_count=2,
                finding_count=1,
                updated_at=_timestamp(),
            )
        ]

    def list_health_scores(self, principal: SecurityPrincipal, limit: int = 5) -> list[AnalysisHealthScore]:
        _ = principal, limit
        return [
            AnalysisHealthScore(
                scope_kind="service",
                scope_name="auth-api",
                score=45,
                status="critical",
                finding_count=1,
                incident_count=1,
                last_seen_at=_timestamp(),
                primary_reason="Denied attempts are rising in the auth path.",
            )
        ]


def _principal() -> SecurityPrincipal:
    """Build a tenant-scoped principal for unit tests."""

    now = _timestamp()
    return SecurityPrincipal(
        subject="copilot-tester",
        tenant_id="payments",
        roles=("alerts:read", "analysis:read", "telemetry:read"),
        issued_at=now,
        expires_at=now,
        issuer="nexusai",
        audience="nexusai-web",
    )


def _finding(
    *,
    finding_id: str,
    incident_id: str,
    category: str,
    severity: str,
    title: str,
    summary: str,
) -> AnalysisFindingRecord:
    """Build a finding row for the copilot test double."""

    observed_at = _timestamp()
    return AnalysisFindingRecord(
        id=finding_id,
        tenant_id="payments",
        incident_id=incident_id,
        telemetry_signal_id=f"sig-{finding_id}",
        correlation_key="payments|auth-api|security-burst",
        source_name="local-otel-collector",
        source_type="otlp",
        observed_at=observed_at,
        batch_label="auth-burst",
        category=category,
        kind="event",
        severity=severity,
        title=title,
        summary=summary,
        confidence=0.92,
        evidence={},
        recommendations=["Review the suspicious login source."],
        service_name="auth-api",
        workload_name="auth-deployment",
        cluster_name="prod-cluster-a",
        namespace="platform",
        created_at=observed_at,
    )


def _incident(
    *,
    incident_id: str,
    state: str,
    confidence: float,
    probable_cause: str,
    evidence_count: int,
    finding_count: int,
    updated_at: datetime,
) -> AnalysisIncidentRecord:
    """Build an incident row for the copilot test double."""

    created_at = _timestamp()
    return AnalysisIncidentRecord(
        id=incident_id,
        tenant_id="payments",
        correlation_key="payments|auth-api|security-burst",
        scope_kind="service",
        scope_name="auth-api",
        state=state,
        title="Security activity is increasing across auth-api",
        summary="The workspace is seeing a suspicious auth burst and the responder should review it.",
        probable_cause=probable_cause,
        confidence=confidence,
        evidence_count=evidence_count,
        finding_count=finding_count,
        service_name="auth-api",
        workload_name="auth-deployment",
        cluster_name="prod-cluster-a",
        namespace="platform",
        recommendations=["Review the suspicious login source."],
        created_at=created_at,
        updated_at=updated_at,
        resolved_at=None,
    )


def _timestamp() -> datetime:
    """Return a stable timestamp for deterministic assertions."""

    return datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

