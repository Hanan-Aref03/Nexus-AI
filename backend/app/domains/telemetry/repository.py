"""Persistence helpers for normalized telemetry."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.domains.telemetry.models import TelemetrySignalRecord
from app.domains.telemetry.schemas import TelemetryIngestRequest, TelemetrySignalIn, TelemetrySignalOut


class TelemetryRepository:
    """Tiny repository that keeps persistence logic separate from routing."""

    def __init__(self, session: Session):
        self._session = session

    def save_signals(
        self,
        batch: TelemetryIngestRequest,
        signals: list[TelemetrySignalIn],
    ) -> list[TelemetrySignalRecord]:
        """Persist one normalized batch and return the stored rows."""

        records: list[TelemetrySignalRecord] = []
        now = datetime.now(timezone.utc)

        for signal in signals:
            records.append(
                TelemetrySignalRecord(
                    id=signal.signal_id or str(uuid4()),
                    source_name=batch.source_name,
                    source_type=batch.source_type.value,
                    kind=signal.kind.value,
                    severity=signal.severity.value,
                    summary=signal.summary,
                    description=signal.description,
                    observed_at=signal.observed_at or now,
                    received_at=now,
                    batch_label=batch.batch_label,
                    service_name=signal.resource.service_name,
                    cluster_name=signal.resource.cluster_name,
                    workload_name=signal.resource.workload_name,
                    namespace=signal.resource.namespace,
                    resource_type=signal.resource.resource_type,
                    resource_name=signal.resource.resource_name,
                    resource=signal.resource.model_dump(mode="json"),
                    attributes=signal.attributes,
                    payload=signal.payload,
                )
            )

        self._session.add_all(records)
        self._session.commit()
        return records

    def list_recent_signals(self, limit: int = 20) -> list[TelemetrySignalRecord]:
        """Return the most recent stored telemetry signals."""

        statement: Select[tuple[TelemetrySignalRecord]] = (
            select(TelemetrySignalRecord)
            .order_by(desc(TelemetrySignalRecord.observed_at), desc(TelemetrySignalRecord.received_at))
            .limit(limit)
        )
        return list(self._session.scalars(statement))

    def to_out(self, record: TelemetrySignalRecord) -> TelemetrySignalOut:
        """Convert ORM rows into API response payloads."""

        return TelemetrySignalOut.model_validate(record)

