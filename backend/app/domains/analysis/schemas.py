"""Pydantic schemas for the detection-core phase."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.telemetry.schemas import TelemetrySeverity, TelemetrySignalKind, TelemetrySourceType


class AnalysisFindingCategory(str, Enum):
    """Top-level anomaly families produced by the deterministic rules."""

    reliability = "reliability"
    capacity = "capacity"
    security = "security"
    performance = "performance"
    anomaly = "anomaly"


class AnalysisScopeKind(str, Enum):
    """Operational scope used to group incidents and health scores."""

    service = "service"
    workload = "workload"
    cluster = "cluster"
    namespace = "namespace"


class AnalysisIncidentState(str, Enum):
    """Lifecycle states supported by the phase-2 incident workflow."""

    open = "open"
    acknowledged = "acknowledged"
    investigating = "investigating"
    resolved = "resolved"


class AnalysisHealthStatus(str, Enum):
    """Human-readable health buckets for the dashboard surface."""

    healthy = "healthy"
    watch = "watch"
    degraded = "degraded"
    critical = "critical"


class AnalysisEvidenceItem(BaseModel):
    """A compact evidence row attached to an incident detail response."""

    finding_id: str
    telemetry_signal_id: str
    title: str
    summary: str
    category: AnalysisFindingCategory
    severity: TelemetrySeverity
    confidence: float


class AnalysisFindingOut(BaseModel):
    """Persisted detection output returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    incident_id: str
    telemetry_signal_id: str
    correlation_key: str
    source_name: str
    source_type: TelemetrySourceType
    observed_at: datetime
    batch_label: str | None
    category: AnalysisFindingCategory
    kind: TelemetrySignalKind
    severity: TelemetrySeverity
    title: str
    summary: str
    confidence: float
    evidence: dict[str, Any]
    recommendations: list[str]
    service_name: str | None
    workload_name: str | None
    cluster_name: str | None
    namespace: str | None
    created_at: datetime


class AnalysisIncidentOut(BaseModel):
    """Incident summary returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    correlation_key: str
    scope_kind: AnalysisScopeKind
    scope_name: str
    state: AnalysisIncidentState
    title: str
    summary: str
    probable_cause: str
    confidence: float
    evidence_count: int
    finding_count: int
    recommendations: list[str]
    service_name: str | None
    workload_name: str | None
    cluster_name: str | None
    namespace: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    evidence: list[AnalysisEvidenceItem] = Field(default_factory=list)


class AnalysisHealthScore(BaseModel):
    """Health score for a service or workload scope."""

    scope_kind: AnalysisScopeKind
    scope_name: str
    score: int
    status: AnalysisHealthStatus
    finding_count: int
    incident_count: int
    last_seen_at: datetime | None
    primary_reason: str


class AnalysisRunResult(BaseModel):
    """Summary response emitted by the analysis runner."""

    processed_signals: int
    created_findings: int
    created_incidents: int
    updated_incidents: int
    health_scores: list[AnalysisHealthScore]


class AnalysisIncidentUpdateRequest(BaseModel):
    """Payload for moving an incident through its lifecycle."""

    state: AnalysisIncidentState

