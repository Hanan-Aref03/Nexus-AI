"""SQLAlchemy models for the Phase 2 detection core."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base


class AnalysisIncidentRecord(Base):
    """Correlated set of findings representing one operational incident."""

    __tablename__ = "analysis_incidents"
    __table_args__ = (
        Index("ix_analysis_incidents_tenant_id", "tenant_id"),
        Index("ix_analysis_incidents_state", "state"),
        Index("ix_analysis_incidents_correlation_key", "correlation_key"),
        Index("ix_analysis_incidents_scope_kind", "scope_kind"),
        Index("ix_analysis_incidents_scope_name", "scope_name"),
        Index("ix_analysis_incidents_updated_at", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="local-tenant",
        server_default=text("'local-tenant'"),
    )
    correlation_key: Mapped[str] = mapped_column(String(255), nullable=False)
    scope_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    scope_name: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        server_default=text("'open'"),
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    probable_cause: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    finding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    service_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    workload_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cluster_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    namespace: Mapped[str | None] = mapped_column(String(120), nullable=True)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AnalysisFindingRecord(Base):
    """One classified signal that contributes to an incident."""

    __tablename__ = "analysis_findings"
    __table_args__ = (
        Index("ix_analysis_findings_tenant_id", "tenant_id"),
        Index("ix_analysis_findings_incident_id", "incident_id"),
        Index("ix_analysis_findings_telemetry_signal_id", "telemetry_signal_id", unique=True),
        Index("ix_analysis_findings_category", "category"),
        Index("ix_analysis_findings_severity", "severity"),
        Index("ix_analysis_findings_service_name", "service_name"),
        Index("ix_analysis_findings_workload_name", "workload_name"),
        Index("ix_analysis_findings_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="local-tenant",
        server_default=text("'local-tenant'"),
    )
    incident_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_incidents.id", ondelete="CASCADE"),
        nullable=False,
    )
    telemetry_signal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("telemetry_signals.id", ondelete="CASCADE"),
        nullable=False,
    )
    correlation_key: Mapped[str] = mapped_column(String(255), nullable=False)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    batch_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    service_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    workload_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cluster_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    namespace: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


class AnalysisEvaluationRecord(Base):
    """Internal ledger of analyzed telemetry signals.

    The ledger keeps the detection runner idempotent by marking both anomalous
    and benign signals as processed.
    """

    __tablename__ = "analysis_evaluations"
    __table_args__ = (
        Index("ix_analysis_evaluations_tenant_id", "tenant_id"),
        Index("ix_analysis_evaluations_telemetry_signal_id", "telemetry_signal_id", unique=True),
        Index("ix_analysis_evaluations_outcome", "outcome"),
        Index("ix_analysis_evaluations_category", "category"),
        Index("ix_analysis_evaluations_evaluated_at", "evaluated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="local-tenant",
        server_default=text("'local-tenant'"),
    )
    telemetry_signal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("telemetry_signals.id", ondelete="CASCADE"),
        nullable=False,
    )
    correlation_key: Mapped[str] = mapped_column(String(255), nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    finding_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("analysis_findings.id", ondelete="SET NULL"),
        nullable=True,
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

