"""SQLAlchemy models for normalized telemetry storage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Index, JSON, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base


class TelemetrySignalRecord(Base):
    """Single normalized telemetry event stored by the foundation."""

    __tablename__ = "telemetry_signals"
    __table_args__ = (
        Index("ix_telemetry_signals_tenant_id", "tenant_id"),
        Index("ix_telemetry_signals_source_type", "source_type"),
        Index("ix_telemetry_signals_kind", "kind"),
        Index("ix_telemetry_signals_service_name", "service_name"),
        Index("ix_telemetry_signals_observed_at", "observed_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="local-tenant",
        server_default=text("'local-tenant'"),
    )
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_subject: Mapped[str | None] = mapped_column(String(120), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    batch_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    service_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cluster_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    workload_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    namespace: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
