"""Deterministic rules for building a compact alert feed.

The Phase 4 slice keeps alerts derived from the existing analysis layer so the
workspace can show a helpful inbox without a separate alert store yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Sequence

from app.domains.analysis.models import AnalysisFindingRecord, AnalysisIncidentRecord
from app.domains.analysis.schemas import AnalysisHealthScore, AnalysisIncidentState, AnalysisScopeKind
from app.domains.telemetry.schemas import TelemetrySeverity


SEVERITY_ORDER = {
    TelemetrySeverity.critical.value: 4,
    TelemetrySeverity.error.value: 3,
    TelemetrySeverity.warning.value: 2,
    TelemetrySeverity.info.value: 1,
    TelemetrySeverity.debug.value: 0,
}


@dataclass(frozen=True, slots=True)
class AlertDraft:
    """Intermediate representation used before the alert feed response."""

    alert_id: str
    kind: str
    severity: TelemetrySeverity
    scope_kind: AnalysisScopeKind
    scope_name: str
    title: str
    summary: str
    source_label: str
    source_detail: str
    action_label: str
    href: str
    confidence: float
    evidence_count: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    slack_preview: str


@dataclass(frozen=True, slots=True)
class AlertsFeedDraft:
    """Whole feed assembled from the current tenant state."""

    mode: str
    generated_at: datetime
    source_label: str
    source_reason: str
    alerts: list[AlertDraft]
    copilot_prompt: str
    slack_preview: str


def _enum_text(value: Any) -> str:
    """Return a stable string for either enums or raw values."""

    if isinstance(value, Enum):
        return value.value
    return str(value)


def _severity_key(value: TelemetrySeverity | str) -> int:
    """Map an alert severity to a sortable score."""

    return SEVERITY_ORDER.get(_enum_text(value), 0)


def _has_security_evidence(incident: AnalysisIncidentRecord, findings: Sequence[AnalysisFindingRecord]) -> bool:
    """Return ``True`` when the incident includes security-oriented evidence."""

    if "security" in incident.probable_cause.lower():
        return True

    for evidence in incident.recommendations:
        if "security" in evidence.lower():
            return True

    for finding in findings:
        if _enum_text(finding.category) == "security":
            return True

    return False


def _incident_severity(incident: AnalysisIncidentRecord) -> TelemetrySeverity:
    """Translate an incident into a Slack-friendly severity."""

    state = _enum_text(incident.state)
    if state == AnalysisIncidentState.resolved.value:
        return TelemetrySeverity.info
    if state == AnalysisIncidentState.open.value:
        return TelemetrySeverity.critical if incident.confidence >= 0.9 or incident.evidence_count >= 3 else TelemetrySeverity.warning
    if state in {AnalysisIncidentState.acknowledged.value, AnalysisIncidentState.investigating.value}:
        return TelemetrySeverity.warning
    return TelemetrySeverity.info


def _health_severity(score: AnalysisHealthScore) -> TelemetrySeverity:
    """Translate a health score into an alert severity."""

    if score.status.value == "critical":
        return TelemetrySeverity.critical
    if score.status.value == "degraded":
        return TelemetrySeverity.warning
    return TelemetrySeverity.info


def _incident_tags(incident: AnalysisIncidentRecord, findings: Sequence[AnalysisFindingRecord]) -> list[str]:
    """Build tags that make the alert inbox easy to scan."""

    tags = [
        _enum_text(incident.state),
        _enum_text(incident.scope_kind),
    ]
    if _has_security_evidence(incident, findings):
        tags.append("security")
    return tags


def _sort_alerts(alerts: Iterable[AlertDraft]) -> list[AlertDraft]:
    """Sort alerts from most urgent to least urgent."""

    return sorted(alerts, key=lambda item: (_severity_key(item.severity), item.updated_at), reverse=True)


def build_incident_alert(incident: AnalysisIncidentRecord, findings: Sequence[AnalysisFindingRecord]) -> AlertDraft | None:
    """Turn one incident into an alert card."""

    if _enum_text(incident.state) == AnalysisIncidentState.resolved.value:
        return None

    severity = _incident_severity(incident)
    tags = _incident_tags(incident, findings)
    if "security" in tags:
        severity = TelemetrySeverity.critical

    source_label = f"{_enum_text(incident.scope_kind).replace('_', ' ').title()} {incident.scope_name}"
    source_detail = f"{incident.evidence_count} evidence item(s) across {incident.finding_count} finding(s)"
    slack_preview = f"{incident.title} | {incident.probable_cause}"

    return AlertDraft(
        alert_id=f"incident-{incident.id}",
        kind="incident",
        severity=severity,
        scope_kind=AnalysisScopeKind(_enum_text(incident.scope_kind)),
        scope_name=incident.scope_name,
        title=incident.title,
        summary=incident.summary,
        source_label=source_label,
        source_detail=source_detail,
        action_label="Open incident",
        href=f"/incidents/{incident.id}",
        confidence=float(incident.confidence),
        evidence_count=incident.evidence_count,
        tags=tags,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        slack_preview=slack_preview,
    )


def build_health_alert(score: AnalysisHealthScore) -> AlertDraft | None:
    """Turn a degraded health score into an alert card."""

    if score.status.value == "healthy":
        return None

    severity = _health_severity(score)
    source_label = f"{_enum_text(score.scope_kind).replace('_', ' ').title()} {score.scope_name}"
    source_detail = f"{score.finding_count} finding(s) across {score.incident_count} incident(s)"
    slack_preview = f"{score.scope_name} is {score.status.value} at {score.score}/100. {score.primary_reason}"
    observed_at = score.last_seen_at or datetime.now(timezone.utc)

    return AlertDraft(
        alert_id=f"health-{_enum_text(score.scope_kind)}-{score.scope_name}",
        kind="health",
        severity=severity,
        scope_kind=score.scope_kind,
        scope_name=score.scope_name,
        title=f"{score.scope_name} health score is {score.score}",
        summary=score.primary_reason,
        source_label=source_label,
        source_detail=source_detail,
        action_label="Open impact map",
        href="/graph",
        confidence=round(score.score / 100, 2),
        evidence_count=score.finding_count,
        tags=[_enum_text(score.scope_kind), score.status.value],
        created_at=observed_at,
        updated_at=observed_at,
        slack_preview=slack_preview,
    )


def build_alert_feed(
    findings: Sequence[AnalysisFindingRecord],
    incidents: Sequence[AnalysisIncidentRecord],
    health_scores: Sequence[AnalysisHealthScore],
    *,
    mode: str,
    source_label: str,
    source_reason: str,
) -> AlertsFeedDraft:
    """Build a single feed that can be rendered in the workspace and Slack later."""

    findings_by_incident: dict[str, list[AnalysisFindingRecord]] = {}
    for finding in findings:
        findings_by_incident.setdefault(finding.incident_id, []).append(finding)

    alerts: list[AlertDraft] = []
    now = datetime.now(timezone.utc)

    for incident in incidents:
        draft = build_incident_alert(incident, findings_by_incident.get(incident.id, []))
        if draft is not None:
            alerts.append(draft)

    for score in health_scores:
        draft = build_health_alert(score)
        if draft is not None:
            alerts.append(draft)

    alerts = _sort_alerts(alerts)

    if alerts:
        top_alert = alerts[0]
        copilot_prompt = _build_copilot_prompt(top_alert)
        slack_preview = _build_slack_preview(top_alert)
    else:
        copilot_prompt = "The workspace is calm right now. Which service should we inspect next?"
        slack_preview = "No active alerts are ready for delivery."

    return AlertsFeedDraft(
        mode=mode,
        generated_at=now,
        source_label=source_label,
        source_reason=source_reason,
        alerts=alerts,
        copilot_prompt=copilot_prompt,
        slack_preview=slack_preview,
    )


def _build_copilot_prompt(alert: AlertDraft) -> str:
    """Generate a concise follow-up question for the future copilot UI."""

    if alert.kind == "incident" and "security" in alert.tags:
        return f"What evidence supports the security incident in {alert.scope_name}, and what should we do first?"

    if alert.kind == "incident":
        return f"What evidence explains the incident in {alert.scope_name}, and what is the safest next step?"

    return f"Why is {alert.scope_name} degraded, and which follow-up should we review first?"


def _build_slack_preview(alert: AlertDraft) -> str:
    """Format a compact Slack-style preview without talking to Slack yet."""

    return f"[{alert.severity.value.upper()}] {alert.title} - {alert.summary} | {alert.action_label}"
