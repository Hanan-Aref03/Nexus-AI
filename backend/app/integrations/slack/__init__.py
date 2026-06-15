"""Slack connector seam for alert delivery."""

from app.integrations.slack.base import SlackConnector, SlackDeliveryDraft
from app.integrations.slack.factory import build_slack_connector
from app.integrations.slack.local import LocalSlackConnector

__all__ = [
    "LocalSlackConnector",
    "SlackConnector",
    "SlackDeliveryDraft",
    "build_slack_connector",
]

