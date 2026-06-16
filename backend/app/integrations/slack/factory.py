"""Factory helpers for the Slack connector seam."""

from __future__ import annotations

from app.core.config import Settings
from app.integrations.slack.base import SlackConnector
from app.integrations.slack.local import LocalSlackConnector


def build_slack_connector(settings: Settings) -> SlackConnector:
    """Create the local Slack connector used until a live transport is added."""

    return LocalSlackConnector(channel=settings.slack_channel)

