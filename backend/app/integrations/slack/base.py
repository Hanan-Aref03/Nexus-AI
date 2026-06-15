"""Slack connector contracts for alert delivery."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domains.alerts.rules import AlertsFeedDraft


@dataclass(frozen=True, slots=True)
class SlackDeliveryDraft:
    """Structured payload prepared for Slack or the local preview."""

    channel: str
    headline: str
    body: str
    preview: str
    alert_count: int
    top_alert_id: str | None
    top_alert_severity: str | None
    top_alert_scope: str | None
    security_signal: bool
    source_label: str
    source_reason: str


class SlackConnector(ABC):
    """Contract for turning an alert feed into a Slack-ready payload."""

    channel: str

    @abstractmethod
    def build_delivery(self, feed: AlertsFeedDraft) -> SlackDeliveryDraft:
        """Translate the alert feed into a delivery draft."""

