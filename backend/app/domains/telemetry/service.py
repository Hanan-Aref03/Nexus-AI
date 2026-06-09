"""Telemetry ingestion service.

The service coordinates source adapters, persistence, and the response payload
so routes stay thin and readable.
"""

from __future__ import annotations

from app.domains.telemetry.adapters.base import AdapterRegistry
from app.domains.telemetry.repository import TelemetryRepository
from app.domains.telemetry.schemas import (
    TelemetryIngestRequest,
    TelemetryIngestResult,
    TelemetrySignalOut,
)


class TelemetryIngestService:
    """Orchestrates normalization and persistence for one intake request."""

    def __init__(self, adapter_registry: AdapterRegistry, repository: TelemetryRepository):
        self._adapter_registry = adapter_registry
        self._repository = repository

    def ingest(self, batch: TelemetryIngestRequest) -> TelemetryIngestResult:
        """Normalize a batch and persist the resulting signals."""

        adapter = self._adapter_registry.get(batch.source_type)
        normalized_signals = adapter.normalize(batch)
        stored_records = self._repository.save_signals(batch=batch, signals=normalized_signals)

        return TelemetryIngestResult(
            source_name=batch.source_name,
            source_type=batch.source_type,
            adapter_status=adapter.status,  # type: ignore[arg-type]
            accepted_signals=len(batch.signals),
            stored_signals=len(stored_records),
            record_ids=[record.id for record in stored_records],
        )

    def list_recent_signals(self, limit: int = 20) -> list[TelemetrySignalOut]:
        """Return the latest stored normalized signals for inspection."""

        return [self._repository.to_out(record) for record in self._repository.list_recent_signals(limit=limit)]

