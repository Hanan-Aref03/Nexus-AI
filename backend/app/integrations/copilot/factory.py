"""Factory helpers for the copilot provider chain."""

from __future__ import annotations

from app.core.config import Settings
from app.integrations.copilot.base import CopilotProviderChain
from app.integrations.copilot.gemini import GeminiCopilotProvider
from app.integrations.copilot.grok import GrokCopilotProvider
from app.integrations.copilot.local import LocalCopilotProvider


def build_copilot_provider_chain(settings: Settings) -> CopilotProviderChain:
    """Create the provider chain in free-to-local fallback order."""

    return CopilotProviderChain(
        providers=[
            GeminiCopilotProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                timeout_seconds=settings.copilot_timeout_seconds,
            ),
            GrokCopilotProvider(
                api_key=settings.xai_api_key,
                model=settings.xai_model,
                timeout_seconds=settings.copilot_timeout_seconds,
            ),
            LocalCopilotProvider(),
        ]
    )

