"""Pydantic schemas for the Phase 4 alert feed."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.domains.analysis.schemas import AnalysisScopeKind
from app.domains.telemetry.schemas import TelemetrySeverity


class AlertKind(str, Enum):
    """Alert families shown in the inbox."""

    incident = "incident"
    health = "health"


class AlertSummary(BaseModel):
    """Compact feed statistics used by the workspace header."""

    total: int
    incidents: int
    health: int
    security: int
    critical: int
    warning: int
    info: int
    scopes: int


class AlertOut(BaseModel):
    """A single alert card in the workspace inbox."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    kind: AlertKind
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


class AlertsFeedOut(BaseModel):
    """Feed returned by the alerts endpoint."""

    mode: str
    generated_at: datetime
    source_label: str
    source_reason: str
    summary: AlertSummary
    copilot_prompt: str
    slack_preview: str
    alerts: list[AlertOut]

