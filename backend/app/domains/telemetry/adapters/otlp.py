"""OpenTelemetry-first adapter for the PR1 foundation."""

from __future__ import annotations

from app.domains.telemetry.adapters.base import TelemetrySourceAdapter
from app.domains.telemetry.schemas import TelemetryIngestRequest, TelemetrySignalIn, TelemetrySourceType


class OtlpTelemetryAdapter(TelemetrySourceAdapter):
    """Free/local adapter that mirrors the OpenTelemetry collector path."""

    source_type = TelemetrySourceType.otlp
    display_name = "OpenTelemetry"
    status = "ready"
    deployment_model = "free-local"
    description = "OpenTelemetry-friendly intake path for collector-forwarded batches."

    def normalize(self, batch: TelemetryIngestRequest) -> list[TelemetrySignalIn]:
        """Phase 1 treats OTLP batches as already normalized signal envelopes."""

        return list(batch.signals)

