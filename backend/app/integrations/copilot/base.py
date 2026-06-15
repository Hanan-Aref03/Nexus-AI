"""Base contracts for copilot providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class CopilotContext:
    """Prompt context extracted from the current tenant evidence."""

    mode: str
    source_label: str
    source_reason: str
    summary_lines: tuple[str, ...]
    evidence_lines: tuple[str, ...]
    top_alert_title: str | None
    top_alert_scope: str | None
    top_alert_severity: str | None


@dataclass(frozen=True, slots=True)
class CopilotReply:
    """Normalized answer returned by any copilot provider."""

    provider: str
    answer: str
    confidence: float
    follow_up: str
    evidence: list[str]
    used_fallback: bool = False


class CopilotProvider(ABC):
    """Base class for live or local copilot implementations."""

    provider_name: str

    def is_configured(self) -> bool:
        """Return ``True`` when the provider can be used in this environment."""

        return True

    @abstractmethod
    def answer(self, question: str, context: CopilotContext) -> CopilotReply:
        """Return a concise, evidence-backed answer."""


class CopilotProviderChain:
    """Try the configured providers in order and keep a local fallback last."""

    def __init__(self, providers: Iterable[CopilotProvider]):
        self._providers = tuple(providers)

    def answer(self, question: str, context: CopilotContext) -> CopilotReply:
        """Return the first successful answer from the provider chain."""

        last_error: Exception | None = None
        for provider in self._providers:
            if not provider.is_configured():
                continue

            try:
                reply = provider.answer(question, context)
            except Exception as exc:  # pragma: no cover - network specific fallback
                last_error = exc
                continue

            return CopilotReply(
                provider=reply.provider,
                answer=reply.answer,
                confidence=reply.confidence,
                follow_up=reply.follow_up,
                evidence=reply.evidence,
                used_fallback=provider.provider_name == "local" or reply.used_fallback,
            )

        if last_error is not None:  # pragma: no cover - defensive fallback
            _ = last_error
        raise RuntimeError("No copilot provider is configured.")

