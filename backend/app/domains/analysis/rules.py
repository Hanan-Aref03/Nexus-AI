"""Deterministic anomaly rules for the Phase 2 detection core."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Iterable, Sequence
from uuid import uuid4

from app.core.redaction import redact_mapping
from app.domains.analysis.schemas import (
    AnalysisFindingCategory,
    AnalysisHealthScore,
    AnalysisHealthStatus,
    AnalysisIncidentState,
    AnalysisScopeKind,
)
from app.domains.telemetry.models import TelemetrySignalRecord


SEVERITY_ORDER = {
    "debug": 0,
    "info": 1,
    "warning": 2,
    "error": 3,
    "critical": 4,
}

SEVERITY_PENALTIES = {
    "debug": 0,
    "info": 0,
    "warning": 8,
    "error": 18,
    "critical": 30,
}

CATEGORY_PENALTIES = {
    AnalysisFindingCategory.anomaly: 4,
    AnalysisFindingCategory.reliability: 8,
    AnalysisFindingCategory.capacity: 10,
    AnalysisFindingCategory.performance: 8,
    AnalysisFindingCategory.security: 15,
}

SECURITY_KEYWORDS = ("unauthorized", "forbidden", "privilege", "auth", "login", "credential", "token", "suspicious")
RELIABILITY_KEYWORDS = ("timeout", "timed out", "error", "failed", "failure", "exception", "unavailable", "5xx", "crash")
CAPACITY_KEYWORDS = ("memory", "cpu", "disk", "saturation", "pressure", "capacity", "utilization", "threshold")
PERFORMANCE_KEYWORDS = ("latency", "slow", "delay", "throughput", "p95", "p99", "bottleneck")


@dataclass(frozen=True, slots=True)
class AnalysisFindingDraft:
    """Intermediate representation used before persistence."""

    finding_id: str
    telemetry_signal_id: str
    correlation_key: str
    scope_kind: AnalysisScopeKind
    scope_name: str
    category: AnalysisFindingCategory
    kind: str
    severity: str
    title: str
    summary: str
    confidence: float
    evidence: dict[str, Any]
    recommendations: list[str]
    source_name: str
    source_type: str
    observed_at: datetime
    batch_label: str | None
    service_name: str | None
    workload_name: str | None
    cluster_name: str | None
    namespace: str | None


@dataclass(frozen=True, slots=True)
class AnalysisIncidentDraft:
    """Intermediate incident summary built from one correlation group."""

    correlation_key: str
    scope_kind: AnalysisScopeKind
    scope_name: str
    title: str
    summary: str
    probable_cause: str
    confidence: float
    recommendations: list[str]
    service_name: str | None
    workload_name: str | None
    cluster_name: str | None
    namespace: str | None


def _severity_key(severity: str) -> int:
    """Map a severity label to a stable comparison key."""

    return SEVERITY_ORDER.get(severity, 0)


def _enum_text(value: Any) -> str:
    """Return a stable text representation for either enums or plain strings."""

    if isinstance(value, Enum):
        return value.value
    return str(value)


def _scope_for_signal(signal: TelemetrySignalRecord) -> tuple[AnalysisScopeKind, str]:
    """Pick the most useful human-readable scope for a telemetry signal."""

    if signal.cluster_name:
        return AnalysisScopeKind.cluster, signal.cluster_name
    if signal.workload_name:
        return AnalysisScopeKind.workload, signal.workload_name
    if signal.service_name:
        return AnalysisScopeKind.service, signal.service_name
    if signal.namespace:
        return AnalysisScopeKind.namespace, signal.namespace
    return AnalysisScopeKind.service, signal.resource_name or signal.source_name


def _stringify_mapping(value: Any) -> Any:
    """Convert nested telemetry values into JSON-safe evidence snapshots."""

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, dict):
        return {key: _stringify_mapping(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_stringify_mapping(item) for item in value]

    return value


def _combined_text(signal: TelemetrySignalRecord) -> str:
    """Build a searchable blob from the most useful signal fields."""

    fragments: list[str] = [
        signal.source_name,
        _enum_text(signal.source_type),
        _enum_text(signal.kind),
        _enum_text(signal.severity),
        signal.summary,
        signal.description or "",
        signal.batch_label or "",
        signal.service_name or "",
        signal.workload_name or "",
        signal.cluster_name or "",
        signal.namespace or "",
        signal.resource_name or "",
        str(signal.attributes),
        str(signal.payload),
    ]
    return " ".join(fragment for fragment in fragments if fragment).lower()


def _matched_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    """Return all keywords that appear in the input text."""

    return [keyword for keyword in keywords if keyword in text]


def _threshold_breach(attributes: dict[str, Any], payload: dict[str, Any]) -> bool:
    """Detect a simple numeric threshold breach from normalized telemetry."""

    threshold = attributes.get("threshold")
    if not isinstance(threshold, (int, float)):
        threshold = payload.get("threshold")
    if not isinstance(threshold, (int, float)):
        return False

    candidate_keys = (
        "value",
        "current",
        "usage",
        "utilization",
        "memory_utilization",
        "cpu_utilization",
        "latency",
        "latency_ms",
    )
    for key in candidate_keys:
        candidate = attributes.get(key)
        if isinstance(candidate, (int, float)) and candidate > threshold:
            return True
        candidate = payload.get(key)
        if isinstance(candidate, (int, float)) and candidate > threshold:
            return True

    return False


def _category_from_signal(signal: TelemetrySignalRecord, text: str, threshold_breach: bool) -> AnalysisFindingCategory | None:
    """Assign the anomaly family for one telemetry signal."""

    signal_kind = _enum_text(signal.kind)
    signal_severity = _enum_text(signal.severity)

    if signal_kind == "security_event" or _matched_keywords(text, SECURITY_KEYWORDS):
        return AnalysisFindingCategory.security

    if threshold_breach or _matched_keywords(text, CAPACITY_KEYWORDS):
        return AnalysisFindingCategory.capacity

    if _matched_keywords(text, PERFORMANCE_KEYWORDS):
        return AnalysisFindingCategory.performance

    if signal_severity in {"error", "critical"} or _matched_keywords(text, RELIABILITY_KEYWORDS):
        return AnalysisFindingCategory.reliability

    if signal_severity == "warning":
        return AnalysisFindingCategory.anomaly

    return None


def _confidence_for_signal(severity: str, category: AnalysisFindingCategory, threshold_breach: bool, keyword_count: int) -> float:
    """Calculate a stable confidence score for the generated finding."""

    base = {
        "critical": 0.92,
        "error": 0.84,
        "warning": 0.72,
        "info": 0.58,
        "debug": 0.5,
    }.get(severity, 0.6)

    base += {
        AnalysisFindingCategory.security: 0.08,
        AnalysisFindingCategory.capacity: 0.05,
        AnalysisFindingCategory.performance: 0.05,
        AnalysisFindingCategory.reliability: 0.05,
        AnalysisFindingCategory.anomaly: 0.02,
    }[category]

    if threshold_breach:
        base += 0.05

    if keyword_count > 1:
        base += 0.03

    return round(min(base, 0.97), 2)


def _recommendations_for_category(category: AnalysisFindingCategory, scope_name: str) -> list[str]:
    """Return operator-friendly remediation guidance for a finding."""

    if category == AnalysisFindingCategory.security:
        return [
            f"Review authentication and authorization attempts affecting {scope_name}.",
            "Check recent privilege changes and suspicious API activity.",
        ]

    if category == AnalysisFindingCategory.capacity:
        return [
            f"Inspect resource pressure for {scope_name} and compare it with its request or limit settings.",
            "Scale the workload or reduce hot-path resource consumption if the pressure is sustained.",
        ]

    if category == AnalysisFindingCategory.performance:
        return [
            f"Inspect trace spans and latency hotspots for {scope_name}.",
            "Review recent deployments, cache behavior, and downstream dependency latency.",
        ]

    if category == AnalysisFindingCategory.reliability:
        return [
            f"Check upstream dependencies and retry behavior for {scope_name}.",
            "Review recent deploys, timeout budgets, and error budgets for the affected service.",
        ]

    return [
        f"Review the anomalous telemetry pattern affecting {scope_name}.",
        "Collect a small follow-up sample and compare it with the recent operational baseline.",
    ]


def _probable_cause_for_category(category: AnalysisFindingCategory) -> str:
    """Translate the category into a concise root-cause hypothesis."""

    return {
        AnalysisFindingCategory.security: "Suspicious authentication or authorization activity.",
        AnalysisFindingCategory.capacity: "The workload is approaching a resource threshold or saturation point.",
        AnalysisFindingCategory.performance: "The service is hitting a latency or throughput bottleneck.",
        AnalysisFindingCategory.reliability: "An upstream dependency or application path is failing.",
        AnalysisFindingCategory.anomaly: "The signal diverged from the expected operational baseline.",
    }[category]


def build_finding_draft(signal: TelemetrySignalRecord) -> AnalysisFindingDraft | None:
    """Convert one telemetry signal into a finding draft when it looks anomalous."""

    signal_severity = _enum_text(signal.severity)
    text = _combined_text(signal)
    threshold_breach = _threshold_breach(signal.attributes, signal.payload)
    category = _category_from_signal(signal, text, threshold_breach)
    if category is None:
        return None

    scope_kind, scope_name = _scope_for_signal(signal)
    keyword_sets = [
        _matched_keywords(text, SECURITY_KEYWORDS),
        _matched_keywords(text, RELIABILITY_KEYWORDS),
        _matched_keywords(text, CAPACITY_KEYWORDS),
        _matched_keywords(text, PERFORMANCE_KEYWORDS),
    ]
    matched_keywords = sorted({keyword for group in keyword_sets for keyword in group})

    summary = signal.summary
    if matched_keywords:
        summary = f"{summary} Keywords: {', '.join(matched_keywords)}."

    evidence = redact_mapping(
        _stringify_mapping(
            {
                "signal": {
                    "id": signal.id,
                    "source_name": signal.source_name,
                    "source_type": signal.source_type,
                    "kind": signal.kind,
                    "severity": signal.severity,
                    "summary": signal.summary,
                    "description": signal.description,
                    "observed_at": signal.observed_at,
                    "batch_label": signal.batch_label,
                    "service_name": signal.service_name,
                    "workload_name": signal.workload_name,
                    "cluster_name": signal.cluster_name,
                    "namespace": signal.namespace,
                    "resource": signal.resource,
                    "attributes": signal.attributes,
                    "payload": signal.payload,
                },
                "rule": category.value,
                "threshold_breach": threshold_breach,
                "matched_keywords": matched_keywords,
            }
        )
    )

    confidence = _confidence_for_signal(signal_severity, category, threshold_breach, len(matched_keywords))
    recommendations = _recommendations_for_category(category, scope_name)
    title_map = {
        AnalysisFindingCategory.security: f"{scope_name} shows a security anomaly",
        AnalysisFindingCategory.capacity: f"{scope_name} is under resource pressure",
        AnalysisFindingCategory.performance: f"{scope_name} is showing performance degradation",
        AnalysisFindingCategory.reliability: f"{scope_name} is emitting reliability anomalies",
        AnalysisFindingCategory.anomaly: f"{scope_name} has unexplained anomalous telemetry",
    }

    return AnalysisFindingDraft(
        finding_id=str(uuid4()),
        telemetry_signal_id=signal.id,
        correlation_key=build_correlation_key(signal, scope_name),
        scope_kind=scope_kind,
        scope_name=scope_name,
        category=category,
        kind=signal.kind,
        severity=signal_severity,
        title=title_map[category],
        summary=summary,
        confidence=confidence,
        evidence=evidence,
        recommendations=recommendations,
        source_name=signal.source_name,
        source_type=_enum_text(signal.source_type),
        observed_at=signal.observed_at,
        batch_label=signal.batch_label,
        service_name=signal.service_name,
        workload_name=signal.workload_name,
        cluster_name=signal.cluster_name,
        namespace=signal.namespace,
    )


def build_correlation_key(signal: TelemetrySignalRecord, scope_name: str) -> str:
    """Derive a stable grouping key so related findings become one incident."""

    batch_fragment = signal.batch_label or signal.source_name
    return "|".join(
        fragment
        for fragment in (
            signal.tenant_id,
            scope_name,
            signal.namespace or "",
            batch_fragment,
        )
        if fragment
    )


def build_incident_draft(findings: Sequence[AnalysisFindingDraft]) -> AnalysisIncidentDraft:
    """Summarize a correlated group of findings into one incident draft."""

    if not findings:
        raise ValueError("At least one finding is required to build an incident.")

    primary = max(findings, key=lambda item: (_severity_key(item.severity), item.confidence))
    scope_kind = primary.scope_kind
    scope_name = primary.scope_name
    recommendations: list[str] = []
    for finding in findings:
        for recommendation in finding.recommendations:
            if recommendation not in recommendations:
                recommendations.append(recommendation)

    if len(findings) == 1:
        title = primary.title
        summary = primary.summary
    else:
        title = f"{scope_name}: {len(findings)} correlated anomalies detected"
        summary = " ".join(finding.summary for finding in findings)

    confidence = round(min(0.98, primary.confidence + 0.05 * (len(findings) - 1)), 2)
    probable_cause = _probable_cause_for_category(primary.category)

    return AnalysisIncidentDraft(
        correlation_key=primary.correlation_key,
        scope_kind=scope_kind,
        scope_name=scope_name,
        title=title,
        summary=summary,
        probable_cause=probable_cause,
        confidence=confidence,
        recommendations=recommendations,
        service_name=primary.service_name,
        workload_name=primary.workload_name,
        cluster_name=primary.cluster_name,
        namespace=primary.namespace,
    )


def _health_status(score: int) -> AnalysisHealthStatus:
    """Convert a numeric score into a dashboard-friendly state."""

    if score >= 90:
        return AnalysisHealthStatus.healthy
    if score >= 70:
        return AnalysisHealthStatus.watch
    if score >= 50:
        return AnalysisHealthStatus.degraded
    return AnalysisHealthStatus.critical


def calculate_health_scores(
    findings: Sequence[Any],
    incidents: Sequence[Any],
) -> list[AnalysisHealthScore]:
    """Aggregate active findings into service and workload health scores."""

    incident_state_by_id = {
        getattr(incident, "id"): getattr(incident, "state")
        for incident in incidents
    }

    buckets: dict[tuple[AnalysisScopeKind, str], dict[str, Any]] = {}
    for finding in findings:
        incident_state = _enum_text(incident_state_by_id.get(getattr(finding, "incident_id"), "open"))
        if incident_state == AnalysisIncidentState.resolved.value:
            continue

        severity = _enum_text(getattr(finding, "severity"))
        category = AnalysisFindingCategory(_enum_text(getattr(finding, "category")))
        incident_id = str(getattr(finding, "incident_id"))
        last_seen_at = getattr(finding, "observed_at", None) or getattr(finding, "created_at", None)

        for scope_kind_name, scope_name in (
            (AnalysisScopeKind.service, getattr(finding, "service_name", None)),
            (AnalysisScopeKind.workload, getattr(finding, "workload_name", None)),
        ):
            if not scope_name:
                continue

            bucket = buckets.setdefault(
                (scope_kind_name, scope_name),
                {
                    "score": 100,
                    "finding_count": 0,
                    "incident_ids": set(),
                    "last_seen_at": None,
                    "reasons": [],
                },
            )

            bucket["finding_count"] += 1
            bucket["incident_ids"].add(incident_id)
            penalty_multiplier = 1.0
            if incident_state in {AnalysisIncidentState.acknowledged.value, AnalysisIncidentState.investigating.value}:
                penalty_multiplier = 0.95

            penalty = int((SEVERITY_PENALTIES.get(severity, 0) + CATEGORY_PENALTIES[category]) * penalty_multiplier)
            bucket["score"] -= penalty
            if last_seen_at is not None and (bucket["last_seen_at"] is None or last_seen_at > bucket["last_seen_at"]):
                bucket["last_seen_at"] = last_seen_at
            bucket["reasons"].append((SEVERITY_ORDER.get(severity, 0), getattr(finding, "summary")))

    scores: list[AnalysisHealthScore] = []
    for (scope_kind, scope_name), bucket in buckets.items():
        score = max(0, min(100, bucket["score"] - max(0, bucket["finding_count"] - 1) * 2 - len(bucket["incident_ids"]) * 3))
        reasons = sorted(bucket["reasons"], key=lambda item: item[0], reverse=True)
        primary_reason = reasons[0][1] if reasons else "No active anomalies detected."
        scores.append(
            AnalysisHealthScore(
                scope_kind=scope_kind,
                scope_name=scope_name,
                score=score,
                status=_health_status(score),
                finding_count=bucket["finding_count"],
                incident_count=len(bucket["incident_ids"]),
                last_seen_at=bucket["last_seen_at"],
                primary_reason=primary_reason,
            )
        )

    return sorted(scores, key=lambda item: (item.score, item.scope_name))
