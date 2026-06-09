"""Local sample adapter used by tests and offline development."""

from __future__ import annotations

from app.domains.telemetry.adapters.base import TelemetrySourceAdapter
from app.domains.telemetry.schemas import TelemetryIngestRequest, TelemetrySignalIn, TelemetrySourceType


class SampleTelemetryAdapter(TelemetrySourceAdapter):
    """Pass-through adapter for sample batches created locally."""

    source_type = TelemetrySourceType.sample
    display_name = "Local Sample"
    status = "ready"
    deployment_model = "free-local"
    description = "Pass-through sample telemetry for offline development and tests."

    def normalize(self, batch: TelemetryIngestRequest) -> list[TelemetrySignalIn]:
        """Sample batches are already normalized, so they are returned as-is."""

        return list(batch.signals)

