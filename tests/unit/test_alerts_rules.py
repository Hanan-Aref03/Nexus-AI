"""Unit tests for the Phase 4 alert feed rules."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domains.alerts.rules import build_alert_feed
from app.domains.analysis.models import AnalysisFindingRecord, AnalysisIncidentRecord
from app.domains.analysis.schemas import AnalysisHealthScore


def test_alert_feed_prioritizes_incidents_and_marks_security_signals() -> None:
    """Security evidence should promote the incident alert and appear first."""

    incident = _incident(
        incident_id="inc-001",
        state="open",
        confidence=0.94,
        probable_cause="Suspicious authentication activity is spreading.",
        evidence_count=2,
        finding_count=2,
        updated_at=datetime(2026, 6, 9, 17, 20, tzinfo=timezone.utc),
    )
    findings = [
        _finding(
            finding_id="find-001",
            incident_id="inc-001",
            category="security",
            severity="critical",
            title="Suspicious login burst",
            summary="Denied attempts climbed quickly across the login path.",
        ),
        _finding(
            finding_id="find-002",
            incident_id="inc-001",
            category="performance",
            severity="warning",
            title="Auth latency increased",
            summary="The auth path is taking longer than the normal baseline.",
        ),
    ]
    health_scores = [
        AnalysisHealthScore(
            scope_kind="service",
            scope_name="auth-api",
            score=44,
            status="critical",
            finding_count=2,
            incident_count=1,
            last_seen_at=datetime(2026, 6, 9, 17, 18, tzinfo=timezone.utc),
            primary_reason="Denied attempts and auth latency are both rising.",
        )
    ]

    feed = build_alert_feed(
        findings,
        [incident],
        health_scores,
        mode="live",
        source_label="Live workspace analysis",
        source_reason="Derived from current incidents and health scores.",
    )

    assert feed.mode == "live"
    assert len(feed.alerts) == 2
    assert feed.alerts[0].kind == "incident"
    assert feed.alerts[0].severity.value == "critical"
    assert "security" in feed.alerts[0].tags
    assert feed.copilot_prompt.startswith("What evidence supports the security incident")
    assert "Open incident" in feed.slack_preview


def _finding(
    *,
    finding_id: str,
    incident_id: str,
    category: str,
    severity: str,
    title: str,
    summary: str,
) -> AnalysisFindingRecord:
    """Build a finding row for alert-rule tests."""

    observed_at = datetime(2026, 6, 9, 17, 16, tzinfo=timezone.utc)
    return AnalysisFindingRecord(
        id=finding_id,
        tenant_id="payments",
        incident_id=incident_id,
        telemetry_signal_id=f"sig-{finding_id}",
        correlation_key="payments|auth-api|auth-spike",
        source_name="local-otel-collector",
        source_type="otlp",
        observed_at=observed_at,
        batch_label="auth-spike",
        category=category,
        kind="event",
        severity=severity,
        title=title,
        summary=summary,
        confidence=0.9,
        evidence={},
        recommendations=["Review the suspicious login source."],
        service_name="auth-api",
        workload_name="auth-deployment",
        cluster_name="prod-cluster-a",
        namespace="platform",
        created_at=observed_at,
    )


def _incident(
    incident_id: str,
    *,
    state: str,
    confidence: float,
    probable_cause: str,
    evidence_count: int,
    finding_count: int,
    updated_at: datetime,
) -> AnalysisIncidentRecord:
    """Build an incident row for alert-rule tests."""

    created_at = datetime(2026, 6, 9, 17, 10, tzinfo=timezone.utc)
    return AnalysisIncidentRecord(
        id=incident_id,
        tenant_id="payments",
        correlation_key="payments|auth-api|auth-spike",
        scope_kind="service",
        scope_name="auth-api",
        state=state,
        title="Auth activity is showing suspicious burst behavior",
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
