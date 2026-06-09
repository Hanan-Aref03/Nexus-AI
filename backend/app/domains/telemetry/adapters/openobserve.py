"""Placeholder OpenObserve adapter.

OpenObserve is part of the roadmap, but PR1 keeps the runtime free/local and
focuses on the adapter boundary plus OpenTelemetry-compatible intake.
"""

from __future__ import annotations

from app.domains.telemetry.adapters.base import AdapterNotReadyError, TelemetrySourceAdapter
from app.domains.telemetry.schemas import TelemetryIngestRequest, TelemetrySignalIn, TelemetrySourceType


class OpenObserveTelemetryAdapter(TelemetrySourceAdapter):
    """Stub adapter reserved for a later PR."""

    source_type = TelemetrySourceType.openobserve
    display_name = "OpenObserve"
    status = "planned"
    deployment_model = "future-external"
    description = "Planned OpenObserve connector reserved for a later PR."

    def normalize(self, batch: TelemetryIngestRequest) -> list[TelemetrySignalIn]:
        """OpenObserve wiring is intentionally postponed until the foundation is stable."""

        raise AdapterNotReadyError("OpenObserve ingestion is planned for a later PR.")

