"""Pydantic schemas for telemetry intake, storage, and diagnostics."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelemetrySourceType(str, Enum):
    """Known source families in the PR1 adapter registry."""

    sample = "sample"
    otlp = "otlp"
    cloudwatch = "cloudwatch"
    openobserve = "openobserve"


class TelemetrySignalKind(str, Enum):
    """Normalized telemetry kinds understood by the platform."""

    log = "log"
    metric = "metric"
    trace = "trace"
    event = "event"
    alert = "alert"
    security_event = "security_event"


class TelemetrySeverity(str, Enum):
    """Severity labels used to make early telemetry scans readable."""

    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class TelemetryResource(BaseModel):
    """Normalized resource metadata attached to every telemetry signal."""

    service_name: str | None = None
    cluster_name: str | None = None
    workload_name: str | None = None
    namespace: str | None = None
    resource_type: str | None = None
    resource_name: str | None = None
    cloud_provider: str | None = None
    account_id: str | None = None
    region: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class TelemetrySignalIn(BaseModel):
    """Normalized telemetry accepted by the phase-1 ingestion endpoint."""

    signal_id: str | None = None
    kind: TelemetrySignalKind
    observed_at: datetime | None = None
    summary: str
    description: str | None = None
    severity: TelemetrySeverity = TelemetrySeverity.info
    resource: TelemetryResource = Field(default_factory=TelemetryResource)
    attributes: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)


class TelemetryIngestRequest(BaseModel):
    """Batch request used by the OTel-first intake endpoint."""

    source_name: str = "local-otel-collector"
    source_type: TelemetrySourceType
    batch_label: str | None = None
    signals: list[TelemetrySignalIn] = Field(default_factory=list)

    @field_validator("signals")
    @classmethod
    def require_signals(cls, value: list[TelemetrySignalIn]) -> list[TelemetrySignalIn]:
        """Reject empty ingestion calls so the API stays explicit."""

        if not value:
            raise ValueError("At least one telemetry signal is required.")
        return value


class TelemetrySignalOut(BaseModel):
    """Persisted telemetry returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    source_name: str
    source_type: TelemetrySourceType
    kind: TelemetrySignalKind
    severity: TelemetrySeverity
    summary: str
    description: str | None
    actor_subject: str | None
    observed_at: datetime
    received_at: datetime
    batch_label: str | None
    service_name: str | None
    cluster_name: str | None
    workload_name: str | None
    namespace: str | None
    resource_type: str | None
    resource_name: str | None
    resource: TelemetryResource
    attributes: dict[str, Any]
    payload: dict[str, Any]


class TelemetryIngestResult(BaseModel):
    """Summary response for a successful ingestion."""

    source_name: str
    source_type: TelemetrySourceType
    adapter_status: Literal["ready", "planned"]
    accepted_signals: int
    stored_signals: int
    record_ids: list[str]


class TelemetryAdapterCapability(BaseModel):
    """A human-readable description of an adapter in the registry."""

    source_type: TelemetrySourceType
    display_name: str
    status: Literal["ready", "planned"]
    deployment_model: Literal["free-local", "future-external"]
    description: str


class TelemetryAdapterList(BaseModel):
    """Envelope returned by the adapter discovery endpoint."""

    adapters: list[TelemetryAdapterCapability]


class HealthResponse(BaseModel):
    """Liveness response for the root health endpoint."""

    status: Literal["ok"]
    service: str
    version: str
    environment: str
    telemetry: str


class ReadyDatabaseStatus(BaseModel):
    """Database-specific readiness information."""

    status: Literal["ready", "degraded"]
    checked_at: datetime | None = None
    error: str | None = None


class ReadyResponse(BaseModel):
    """Overall readiness response used by deployment checks."""

    status: Literal["ready", "degraded"]
    service: str
    database: ReadyDatabaseStatus
    adapters: list[TelemetryAdapterCapability]
