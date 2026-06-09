"""Placeholder CloudWatch adapter.

The adapter seam is intentionally present in PR1, but the live integration is
deferred so the foundation stays free/local and easy to run.
"""

from __future__ import annotations

from app.domains.telemetry.adapters.base import AdapterNotReadyError, TelemetrySourceAdapter
from app.domains.telemetry.schemas import TelemetryIngestRequest, TelemetrySignalIn, TelemetrySourceType


class CloudWatchTelemetryAdapter(TelemetrySourceAdapter):
    """Stub adapter reserved for a later PR."""

    source_type = TelemetrySourceType.cloudwatch
    display_name = "AWS CloudWatch"
    status = "planned"
    deployment_model = "future-external"
    description = "Planned AWS connector kept behind the adapter seam for PR2+."

    def normalize(self, batch: TelemetryIngestRequest) -> list[TelemetrySignalIn]:
        """CloudWatch wiring is intentionally postponed until the foundation is stable."""

        raise AdapterNotReadyError("CloudWatch ingestion is planned for a later PR.")

