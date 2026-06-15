"""Grok copilot provider using the xAI REST endpoint."""

from __future__ import annotations

import json
from dataclasses import dataclass
from os import getenv
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.integrations.copilot.base import CopilotContext, CopilotProvider, CopilotReply
from app.integrations.copilot.prompt import build_copilot_prompt, parse_structured_reply


@dataclass(frozen=True, slots=True)
class GrokCopilotProvider(CopilotProvider):
    """Use Grok as the fallback live provider when configured."""

    api_key: str | None
    model: str
    timeout_seconds: float = 12.0

    provider_name: str = "grok"

    def is_configured(self) -> bool:
        """Return `True` when the xAI API key is present."""

        return bool(self.api_key or getenv("XAI_API_KEY"))

    def answer(self, question: str, context: CopilotContext) -> CopilotReply:
        """Call the xAI responses endpoint and normalize the payload."""

        api_key = self.api_key or getenv("XAI_API_KEY")
        if not api_key:
            raise RuntimeError("xAI API key is not configured.")

        prompt = build_copilot_prompt(question, context)
        request = Request(
            "https://api.x.ai/v1/responses",
            data=json.dumps(
                {
                    "model": self.model,
                    "input": [
                        {
                            "role": "system",
                            "content": "You are NexusAI Copilot, an evidence-first assistant for incident response.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    "temperature": 0.2,
                    "max_output_tokens": 512,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:  # pragma: no cover - network specific
            raise RuntimeError("Grok copilot request failed.") from exc

        text = _extract_xai_text(body)
        normalized = parse_structured_reply(text, context.evidence_lines)
        return CopilotReply(
            provider=self.provider_name,
            answer=normalized["answer"],
            confidence=float(normalized["confidence"]),
            follow_up=normalized["follow_up"],
            evidence=list(normalized["evidence"]),
        )


def _extract_xai_text(payload: object) -> str:
    """Extract a text answer from the xAI response payload."""

    if isinstance(payload, dict):
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]
        output = payload.get("output")
        if isinstance(output, list):
            chunks: list[str] = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and isinstance(part.get("text"), str):
                            chunks.append(part["text"])
                elif isinstance(content, str):
                    chunks.append(content)
            if chunks:
                return "\n".join(chunks)

    return ""
