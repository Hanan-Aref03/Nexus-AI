"""Gemini copilot provider using the official REST endpoint."""

from __future__ import annotations

import json
from dataclasses import dataclass
from os import getenv
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.integrations.copilot.base import CopilotContext, CopilotProvider, CopilotReply
from app.integrations.copilot.prompt import build_copilot_prompt, parse_structured_reply


@dataclass(frozen=True, slots=True)
class GeminiCopilotProvider(CopilotProvider):
    """Use Gemini as the preferred free-tier provider when configured."""

    api_key: str | None
    model: str
    timeout_seconds: float = 12.0

    provider_name: str = "gemini"

    def is_configured(self) -> bool:
        """Return `True` when the API key is present."""

        return bool(self.api_key or getenv("GEMINI_API_KEY"))

    def answer(self, question: str, context: CopilotContext) -> CopilotReply:
        """Call the Gemini REST API and normalize the response."""

        api_key = self.api_key or getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        prompt = build_copilot_prompt(question, context)
        request = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            data=json.dumps(
                {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": prompt}],
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 512,
                    },
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:  # pragma: no cover - network specific
            raise RuntimeError("Gemini copilot request failed.") from exc

        text = _extract_gemini_text(body)
        normalized = parse_structured_reply(text, context.evidence_lines)
        return CopilotReply(
            provider=self.provider_name,
            answer=normalized["answer"],
            confidence=float(normalized["confidence"]),
            follow_up=normalized["follow_up"],
            evidence=list(normalized["evidence"]),
        )


def _extract_gemini_text(payload: object) -> str:
    """Extract the first text response from a Gemini API payload."""

    if not isinstance(payload, dict):
        return ""

    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content")
            if not isinstance(content, dict):
                continue
            parts = content.get("parts")
            if not isinstance(parts, list):
                continue
            for part in parts:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    return part["text"]

    return str(payload.get("text") or payload.get("output_text") or "")

