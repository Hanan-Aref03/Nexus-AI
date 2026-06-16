"""Unit tests for the Slack connector seam."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.auth import SecurityPrincipal
from app.core.config import Settings
from app.domains.alerts.rules import build_alert_feed
from app.domains.alerts.services import AlertsService
from app.domains.analysis.models import AnalysisFindingRecord, AnalysisIncidentRecord
from app.domains.analysis.schemas import AnalysisHealthScore
from app.integrations.slack.base import SlackDeliveryDraft
from app.integrations.slack.factory import build_slack_connector


def test_local_slack_connector_builds_a_stable_preview() -> None:
    """The local Slack seam should format the same preview every time."""

    feed = _build_security_alert_feed()
    connector = build_slack_connector(Settings(slack_channel="#ops-alerts"))

    delivery = connector.build_delivery(feed)

    assert delivery.channel == "#ops-alerts"
    assert delivery.alert_count == len(feed.alerts)
    assert delivery.top_alert_id == feed.alerts[0].alert_id
    assert delivery.security_signal is True
    assert delivery.preview == feed.slack_preview


def test_alerts_service_uses_the_slack_connector_preview() -> None:
    """The alert service should prefer the connector preview when one exists."""

    connector = _RecordingSlackConnector()
    service = AlertsService(_EmptyAlertsRepository(), slack_connector=connector)
    principal = _principal()

    response = service.list_alerts(principal=principal, limit=10)

    assert connector.called is True
    assert response.slack_preview == "custom slack preview"
    assert response.copilot_prompt == "The workspace is calm right now. Which service should we inspect next?"


class _EmptyAlertsRepository:
    """Repository double that returns no live alerts."""

    def list_findings(self, principal: SecurityPrincipal, limit: int = 12) -> list[object]:
        _ = principal, limit
        return []

    def list_incidents(self, principal: SecurityPrincipal, limit: int = 12) -> list[object]:
        _ = principal, limit
        return []

    def list_health_scores(self, principal: SecurityPrincipal, limit: int = 12) -> list[object]:
        _ = principal, limit
        return []


class _RecordingSlackConnector:
    """Connector double that makes it easy to verify service wiring."""

    def __init__(self) -> None:
        self.called = False

    def build_delivery(self, feed) -> SlackDeliveryDraft:
        self.called = True
        _ = feed
        return SlackDeliveryDraft(
            channel="#ops-alerts",
            headline="Workspace is calm",
            body="No active alerts are ready for delivery.",
            preview="custom slack preview",
            alert_count=0,
            top_alert_id=None,
            top_alert_severity=None,
            top_alert_scope=None,
            security_signal=False,
            source_label="Sample workspace snapshot",
            source_reason="No live analysis data is present yet.",
        )


def _build_security_alert_feed():
    """Create a deterministic feed with one security-forward incident."""

    incident = AnalysisIncidentRecord(
        id="inc-101",
        tenant_id="payments",
        correlation_key="payments|auth-api|security-burst",
        scope_kind="service",
        scope_name="auth-api",
        state="open",
        title="Security activity is increasing across auth-api",
        summary="The workspace is seeing a suspicious burst of denied authentication attempts.",
        probable_cause="Suspicious authentication activity is spreading.",
        confidence=0.95,
        evidence_count=2,
        finding_count=1,
        service_name="auth-api",
        workload_name="auth-deployment",
        cluster_name="prod-cluster-a",
        namespace="platform",
        recommendations=["Review the suspicious login source."],
        created_at=_timestamp(),
        updated_at=_timestamp(),
        resolved_at=None,
    )
    findings = [
        AnalysisFindingRecord(
            id="find-101",
            tenant_id="payments",
            incident_id="inc-101",
            telemetry_signal_id="sig-101",
            correlation_key="payments|auth-api|security-burst",
            source_name="local-otel-collector",
            source_type="otlp",
            observed_at=_timestamp(),
            batch_label="auth-burst",
            category="security",
            kind="event",
            severity="critical",
            title="Suspicious login burst",
            summary="Denied attempts climbed quickly across the login path.",
            confidence=0.92,
            evidence={},
            recommendations=["Review the suspicious login source."],
            service_name="auth-api",
            workload_name="auth-deployment",
            cluster_name="prod-cluster-a",
            namespace="platform",
            created_at=_timestamp(),
        )
    ]
    health_scores = [
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

    return build_alert_feed(
        findings,
        [incident],
        health_scores,
        mode="live",
        source_label="Live workspace analysis",
        source_reason="Derived from the current incidents and health scores.",
    )


def _principal() -> SecurityPrincipal:
    """Build a tenant-scoped principal for service tests."""

    now = _timestamp()
    return SecurityPrincipal(
        subject="alerts-tester",
        tenant_id="payments",
        roles=("alerts:read", "analysis:read", "telemetry:read"),
        issued_at=now,
        expires_at=now,
        issuer="nexusai",
        audience="nexusai-web",
    )


def _timestamp() -> datetime:
    """Return a stable timestamp for deterministic tests."""

    return datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

