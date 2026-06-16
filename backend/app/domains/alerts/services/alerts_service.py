"""Alert feed orchestration."""

from __future__ import annotations

from collections import Counter

from app.core.auth import SecurityPrincipal
from app.domains.alerts.repositories import AlertsRepository
from app.domains.alerts.rules import AlertDraft, AlertsFeedDraft, build_alert_feed
from app.domains.alerts.schemas import AlertKind, AlertOut, AlertSummary, AlertsFeedOut
from app.integrations.slack.base import SlackConnector


class AlertsService:
    """Assemble a concise alert inbox from the analysis store."""

    def __init__(self, repository: AlertsRepository, slack_connector: SlackConnector | None = None):
        self._repository = repository
        self._slack_connector = slack_connector

    def list_alerts(self, principal: SecurityPrincipal, limit: int = 12) -> AlertsFeedOut:
        """Return the current alert feed for the tenant."""

        findings = self._repository.list_findings(principal, limit=limit)
        incidents = self._repository.list_incidents(principal, limit=limit)
        health_scores = self._repository.list_health_scores(principal, limit=limit)

        has_live_data = bool(findings or incidents or health_scores)
        feed = build_alert_feed(
            findings,
            incidents,
            health_scores,
            mode="live" if has_live_data else "demo",
            source_label="Live workspace analysis" if has_live_data else "Sample workspace snapshot",
            source_reason=(
                "This feed is derived from the current incidents and health scores so Slack and the workspace stay aligned."
                if has_live_data
                else "No live analysis data is present yet, so a calm sample inbox is shown instead."
            ),
        )
        slack_delivery = self._slack_connector.build_delivery(feed) if self._slack_connector is not None else None
        summary = self._summarize(feed)

        return AlertsFeedOut(
            mode=feed.mode,
            generated_at=feed.generated_at,
            source_label=feed.source_label,
            source_reason=feed.source_reason,
            summary=summary,
            copilot_prompt=feed.copilot_prompt,
            slack_preview=slack_delivery.preview if slack_delivery is not None else feed.slack_preview,
            alerts=[self._to_out(principal, item) for item in feed.alerts[:limit]],
        )

    def _to_out(self, principal: SecurityPrincipal, draft: AlertDraft) -> AlertOut:
        """Convert an alert draft into an API-ready payload."""

        return AlertOut.model_validate(
            {
                "id": draft.alert_id,
                "tenant_id": principal.tenant_id,
                "kind": AlertKind(draft.kind),
                "severity": draft.severity,
                "scope_kind": draft.scope_kind,
                "scope_name": draft.scope_name,
                "title": draft.title,
                "summary": draft.summary,
                "source_label": draft.source_label,
                "source_detail": draft.source_detail,
                "action_label": draft.action_label,
                "href": draft.href,
                "confidence": draft.confidence,
                "evidence_count": draft.evidence_count,
                "tags": draft.tags,
                "created_at": draft.created_at,
                "updated_at": draft.updated_at,
                "slack_preview": draft.slack_preview,
            }
        )

    def _summarize(self, feed: AlertsFeedDraft) -> AlertSummary:
        """Produce the counts displayed in the page header."""

        severities = Counter(alert.severity.value for alert in feed.alerts)
        kinds = Counter(alert.kind for alert in feed.alerts)
        security_count = sum(1 for alert in feed.alerts if "security" in alert.tags)
        scopes = {
            (alert.scope_kind.value if hasattr(alert.scope_kind, "value") else str(alert.scope_kind), alert.scope_name)
            for alert in feed.alerts
        }

        return AlertSummary(
            total=len(feed.alerts),
            incidents=kinds.get("incident", 0),
            health=kinds.get("health", 0),
            security=security_count,
            critical=severities.get("critical", 0),
            warning=severities.get("warning", 0),
            info=severities.get("info", 0),
            scopes=len(scopes),
        )
