"""Adapter contracts for PR1 telemetry sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from app.domains.telemetry.schemas import (
    TelemetryAdapterCapability,
    TelemetryIngestRequest,
    TelemetrySignalIn,
    TelemetrySourceType,
)


class AdapterNotReadyError(NotImplementedError):
    """Raised by planned adapters that are not wired yet."""


class TelemetrySourceAdapter(ABC):
    """Base class for source-specific normalization adapters."""

    source_type: TelemetrySourceType
    display_name: str
    status: str
    deployment_model: str
    description: str

    def capability(self) -> TelemetryAdapterCapability:
        """Return a concise capability descriptor for the API."""

        return TelemetryAdapterCapability(
            source_type=self.source_type,
            display_name=self.display_name,
            status=self.status,  # type: ignore[arg-type]
            deployment_model=self.deployment_model,  # type: ignore[arg-type]
            description=self.description,
        )

    @abstractmethod
    def normalize(self, batch: TelemetryIngestRequest) -> list[TelemetrySignalIn]:
        """Convert a source-specific payload into normalized telemetry."""


class AdapterRegistry:
    """Tiny registry that keeps the adapter seam explicit and testable."""

    def __init__(self, adapters: Iterable[TelemetrySourceAdapter]):
        self._adapters = {adapter.source_type: adapter for adapter in adapters}

    def get(self, source_type: TelemetrySourceType) -> TelemetrySourceAdapter:
        """Return the adapter for a specific source type."""

        try:
            return self._adapters[source_type]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise AdapterNotReadyError(f"No adapter registered for {source_type.value}.") from exc

    def capabilities(self) -> list[TelemetryAdapterCapability]:
        """Return all adapter capabilities in a deterministic order."""

        return [
            adapter.capability()
            for adapter in sorted(
                self._adapters.values(),
                key=lambda item: (item.status != "ready", item.source_type.value),
            )
        ]
