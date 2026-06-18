"""Unit tests for the Phase 5 FinOps and predictive reliability lens."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.auth import SecurityPrincipal
from app.domains.analysis.models import AnalysisFindingRecord, AnalysisIncidentRecord
from app.domains.analysis.schemas import AnalysisScopeKind
from app.domains.finops.service import FinOpsService


class _EmptyFinOpsRepository:
    """Repository stub that simulates a calm workspace."""

    def list_findings(self, principal: SecurityPrincipal, limit: int = 100):  # noqa: ARG002
        return []

    def list_incidents(self, principal: SecurityPrincipal, limit: int = 50):  # noqa: ARG002
        return []


class _WorkspaceFinOpsRepository:
    """Repository stub that simulates a pressured production workspace."""

    def __init__(self) -> None:
        self._findings = [
            _finding(
                finding_id="find-001",
                incident_id="inc-001",
                category="capacity",
                severity="warning",
                title="checkout-api capacity pressure is rising",
                summary="The checkout service is seeing memory pressure and a likely rightsizing opportunity.",
                service_name="checkout-api",
                workload_name="checkout-deployment",
            ),
            _finding(
                finding_id="find-002",
                incident_id="inc-001",
                category="performance",
                severity="error",
                title="checkout-api latency is pushing spend upward",
                summary="The checkout path is taking longer than the normal baseline and scaling is becoming expensive.",
                service_name="checkout-api",
                workload_name="checkout-deployment",
            ),
        ]
        self._incidents = [
            _incident(
                incident_id="inc-001",
                state="open",
                title="checkout-api is under pressure",
                summary="The checkout path is trending toward a resource issue.",
                probable_cause="The checkout path is hitting a resource bottleneck.",
                scope_kind="service",
                scope_name="checkout-api",
                service_name="checkout-api",
                workload_name="checkout-deployment",
            )
        ]

    def list_findings(self, principal: SecurityPrincipal, limit: int = 100):  # noqa: ARG002
        return self._findings

    def list_incidents(self, principal: SecurityPrincipal, limit: int = 50):  # noqa: ARG002
        return self._incidents


def test_finops_service_derives_savings_and_forecasts_from_workspace_pressure() -> None:
    """A live workspace should produce savings opportunities and forecasts."""

    service = FinOpsService(_WorkspaceFinOpsRepository())
    insights = service.summarize(_principal())

    assert insights.mode == "live"
    assert insights.estimated_monthly_savings > 0
    assert insights.opportunity_count >= 1
    assert insights.forecast_count >= 1
    assert insights.top_scope == "checkout-api"
    assert insights.opportunities[0].scope_name == "checkout-api"
    assert insights.opportunities[0].estimated_monthly_savings > 0
    assert any(forecast.kind.value == "saturation" for forecast in insights.forecasts)


def test_finops_service_returns_demo_insights_when_workspace_is_calm() -> None:
    """A calm workspace should still get a helpful sample FinOps scenario."""

    service = FinOpsService(_EmptyFinOpsRepository())
    insights = service.summarize(_principal())

    assert insights.mode == "demo"
    assert insights.opportunity_count == 2
    assert insights.forecast_count == 3
    assert insights.estimated_monthly_savings == 284.0
    assert insights.top_scope == "payments-prod"


def _finding(
    *,
    finding_id: str,
    incident_id: str,
    category: str,
    severity: str,
    title: str,
    summary: str,
    service_name: str,
    workload_name: str,
) -> AnalysisFindingRecord:
    """Build a detection finding row for the FinOps tests."""

    observed_at = datetime(2026, 6, 15, 18, 0, tzinfo=timezone.utc)
    return AnalysisFindingRecord(
        id=finding_id,
        tenant_id="payments",
        incident_id=incident_id,
        telemetry_signal_id=f"sig-{finding_id}",
        correlation_key="payments|checkout-api|checkout-demo",
        source_name="local-demo",
        source_type="sample",
        observed_at=observed_at,
        batch_label="phase-5-demo",
        category=category,
        kind="metric" if category == "capacity" else "log",
        severity=severity,
        title=title,
        summary=summary,
        confidence=0.9,
        evidence={},
        recommendations=["Review the resource footprint."],
        service_name=service_name,
        workload_name=workload_name,
        cluster_name="payments-prod",
        namespace="payments",
        created_at=observed_at,
    )


def _incident(
    *,
    incident_id: str,
    state: str,
    title: str,
    summary: str,
    probable_cause: str,
    scope_kind: str,
    scope_name: str,
    service_name: str,
    workload_name: str,
) -> AnalysisIncidentRecord:
    """Build a detection incident row for the FinOps tests."""

    created_at = datetime(2026, 6, 15, 18, 0, tzinfo=timezone.utc)
    return AnalysisIncidentRecord(
        id=incident_id,
        tenant_id="payments",
        correlation_key="payments|checkout-api|checkout-demo",
        scope_kind=scope_kind,
        scope_name=scope_name,
        state=state,
        title=title,
        summary=summary,
        probable_cause=probable_cause,
        confidence=0.91,
        evidence_count=2,
        finding_count=2,
        service_name=service_name,
        workload_name=workload_name,
        cluster_name="payments-prod",
        namespace="payments",
        recommendations=["Inspect the checkout resource footprint."],
        created_at=created_at,
        updated_at=created_at,
        resolved_at=None,
    )


def _principal() -> SecurityPrincipal:
    """Return the authenticated principal used in the FinOps tests."""

    issued_at = datetime(2026, 6, 15, 17, 0, tzinfo=timezone.utc)
    expires_at = datetime(2026, 6, 15, 19, 0, tzinfo=timezone.utc)
    return SecurityPrincipal(
        subject="tester-finops",
        tenant_id="payments",
        roles=("analysis:read",),
        issued_at=issued_at,
        expires_at=expires_at,
        issuer="nexusai",
        audience="nexusai-web",
    )
