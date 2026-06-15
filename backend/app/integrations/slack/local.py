"""Local Slack connector used before any live vendor transport is enabled."""

from __future__ import annotations

from app.domains.alerts.rules import AlertDraft, AlertsFeedDraft
from app.integrations.slack.base import SlackConnector, SlackDeliveryDraft


class LocalSlackConnector(SlackConnector):
    """Build a deterministic Slack delivery draft without calling Slack."""

    def __init__(self, channel: str = "#nexusai-alerts") -> None:
        self.channel = channel

    def build_delivery(self, feed: AlertsFeedDraft) -> SlackDeliveryDraft:
        """Shape a readable Slack payload from the current alert inbox."""

        top_alert = feed.alerts[0] if feed.alerts else None
        if top_alert is None:
            return SlackDeliveryDraft(
                channel=self.channel,
                headline="Workspace is calm",
                body="No active alerts are ready for delivery.",
                preview="No active alerts are ready for delivery.",
                alert_count=0,
                top_alert_id=None,
                top_alert_severity=None,
                top_alert_scope=None,
                security_signal=False,
                source_label=feed.source_label,
                source_reason=feed.source_reason,
            )

        return SlackDeliveryDraft(
            channel=self.channel,
            headline=f"{top_alert.severity.value.upper()} alert for {top_alert.scope_name}",
            body=f"{top_alert.title} - {top_alert.summary}",
            preview=_format_preview(top_alert),
            alert_count=len(feed.alerts),
            top_alert_id=top_alert.alert_id,
            top_alert_severity=top_alert.severity.value,
            top_alert_scope=f"{top_alert.scope_kind.value}:{top_alert.scope_name}",
            security_signal="security" in top_alert.tags,
            source_label=feed.source_label,
            source_reason=feed.source_reason,
        )


def _format_preview(alert: AlertDraft) -> str:
    """Keep the preview text stable while the live transport is still planned."""

    return f"[{alert.severity.value.upper()}] {alert.title} - {alert.summary} | {alert.action_label}"

