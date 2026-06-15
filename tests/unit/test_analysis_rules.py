"""Unit tests for the Phase 2 deterministic analysis rules."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domains.analysis.rules import build_finding_draft, build_incident_draft, calculate_health_scores
from app.domains.analysis.schemas import AnalysisHealthStatus, AnalysisIncidentState
from app.domains.telemetry.models import TelemetrySignalRecord


def _signal(
    *,
    signal_id: str,
    source_name: str,
    source_type: str,
    kind: str,
    severity: str,
    summary: str,
    service_name: str | None,
    workload_name: str | None,
    cluster_name: str | None,
    namespace: str | None,
    batch_label: str | None,
    attributes: dict[str, object],
    payload: dict[str, object],
) -> TelemetrySignalRecord:
    """Build a lightweight telemetry ORM object for rule-engine tests."""

    observed_at = datetime(2026, 6, 9, 17, 0, tzinfo=timezone.utc)
    received_at = datetime(2026, 6, 9, 17, 0, 5, tzinfo=timezone.utc)
    return TelemetrySignalRecord(
        id=signal_id,
        tenant_id="payments",
        source_name=source_name,
        source_type=source_type,
        kind=kind,
        severity=severity,
        summary=summary,
        description=None,
        observed_at=observed_at,
        received_at=received_at,
        batch_label=batch_label,
        service_name=service_name,
        cluster_name=cluster_name,
        workload_name=workload_name,
        namespace=namespace,
        resource_type="kubernetes_pod" if workload_name else "kubernetes_statefulset",
        resource_name=f"{service_name or workload_name}-1",
        resource={
            "service_name": service_name,
            "cluster_name": cluster_name,
            "workload_name": workload_name,
            "namespace": namespace,
        },
        attributes=attributes,
        payload=payload,
    )


def test_signal_rules_group_related_anomalies_into_one_incident() -> None:
    """The demo batch should collapse into one correlated incident."""

    checkout_signal = _signal(
        signal_id="sig-001",
        source_name="local-demo",
        source_type="sample",
        kind="log",
        severity="error",
        summary="Checkout API emitted repeated 500 responses",
        service_name="checkout-api",
        workload_name="checkout-deployment",
        cluster_name="payments-prod",
        namespace="payments",
        batch_label="phase-1-demo",
        attributes={"status_code": 500, "request_count": 42, "window_seconds": 5},
        payload={"message": "upstream dependency timed out", "trace_id": "trace-abc-123"},
    )
    redis_signal = _signal(
        signal_id="sig-002",
        source_name="local-demo",
        source_type="sample",
        kind="metric",
        severity="warning",
        summary="Redis memory usage crossed the warning threshold",
        service_name="redis-cache",
        workload_name="redis-statefulset",
        cluster_name="payments-prod",
        namespace="payments",
        batch_label="phase-1-demo",
        attributes={"memory_utilization": 0.87, "threshold": 0.8},
        payload={"metric_name": "container_memory_working_set_bytes", "value": 861234567},
    )

    checkout_finding = build_finding_draft(checkout_signal)
    redis_finding = build_finding_draft(redis_signal)

    assert checkout_finding is not None
    assert redis_finding is not None
    assert checkout_finding.category.value == "reliability"
    assert redis_finding.category.value == "capacity"
    assert checkout_finding.correlation_key == redis_finding.correlation_key
    assert checkout_finding.evidence["rule"] == "reliability"

    incident = build_incident_draft([checkout_finding, redis_finding])
    assert incident.title == "payments-prod: 2 correlated anomalies detected"
    assert incident.probable_cause == "An upstream dependency or application path is failing."
    assert len(incident.recommendations) == 4


def test_health_scoring_covers_service_and_workload_scopes() -> None:
    """Active findings should score both service and workload health."""

    incident = _incident("inc-001", state="open")
    findings = [
        _finding(
            finding_id="find-001",
            incident_id="inc-001",
            telemetry_signal_id="sig-001",
            category="reliability",
            severity="error",
            summary="Checkout API emitted repeated 500 responses",
            service_name="checkout-api",
            workload_name="checkout-deployment",
        ),
        _finding(
            finding_id="find-002",
            incident_id="inc-001",
            telemetry_signal_id="sig-002",
            category="capacity",
            severity="warning",
            summary="Redis memory usage crossed the warning threshold",
            service_name="redis-cache",
            workload_name="redis-statefulset",
        ),
    ]

    scores = calculate_health_scores(findings, [incident])

    assert {score.scope_name for score in scores} == {
        "checkout-api",
        "checkout-deployment",
        "redis-cache",
        "redis-statefulset",
    }
    assert all(score.score < 100 for score in scores)
    assert {score.status for score in scores} <= {
        AnalysisHealthStatus.watch,
        AnalysisHealthStatus.degraded,
        AnalysisHealthStatus.critical,
    }


def test_resolved_incidents_do_not_penalize_current_health() -> None:
    """Resolved incidents should be ignored when health is recalculated."""

    incident = _incident("inc-002", state=AnalysisIncidentState.resolved.value)
    findings = [
        _finding(
            finding_id="find-003",
            incident_id="inc-002",
            telemetry_signal_id="sig-003",
            category="security",
            severity="critical",
            summary="Suspicious authentication activity detected",
            service_name="auth-api",
            workload_name="auth-deployment",
        )
    ]

    scores = calculate_health_scores(findings, [incident])

    assert scores == []


def _finding(
    *,
    finding_id: str,
    incident_id: str,
    telemetry_signal_id: str,
    category: str,
    severity: str,
    summary: str,
    service_name: str,
    workload_name: str,
) -> AnalysisFindingRecord:
    """Build a detection finding record for health-score tests."""

    from app.domains.analysis.models import AnalysisFindingRecord

    observed_at = datetime(2026, 6, 9, 17, 1, tzinfo=timezone.utc)
    return AnalysisFindingRecord(
        id=finding_id,
        tenant_id="payments",
        incident_id=incident_id,
        telemetry_signal_id=telemetry_signal_id,
        correlation_key="payments|demo|phase-1-demo",
        source_name="local-demo",
        source_type="sample",
        observed_at=observed_at,
        batch_label="phase-1-demo",
        category=category,
        kind="log" if category != "capacity" else "metric",
        severity=severity,
        title=f"{service_name} anomaly",
        summary=summary,
        confidence=0.9,
        evidence={},
        recommendations=["Investigate the issue."],
        service_name=service_name,
        workload_name=workload_name,
        cluster_name="payments-prod",
        namespace="payments",
        created_at=observed_at,
    )


def _incident(incident_id: str, *, state: str) -> "AnalysisIncidentRecord":
    """Build a detection incident record for health-score tests."""

    from app.domains.analysis.models import AnalysisIncidentRecord

    created_at = datetime(2026, 6, 9, 17, 1, tzinfo=timezone.utc)
    return AnalysisIncidentRecord(
        id=incident_id,
        tenant_id="payments",
        correlation_key="payments-prod|phase-1-demo",
        scope_kind="cluster",
        scope_name="payments-prod",
        state=state,
        title="payments-prod: correlated anomalies detected",
        summary="Correlated anomalies were detected.",
        probable_cause="An upstream dependency or application path is failing.",
        confidence=0.9,
        evidence_count=2,
        finding_count=2,
        service_name="checkout-api",
        workload_name="checkout-deployment",
        cluster_name="payments-prod",
        namespace="payments",
        recommendations=["Investigate the issue."],
        created_at=created_at,
        updated_at=created_at,
    )
