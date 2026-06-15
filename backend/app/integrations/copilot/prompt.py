"""Prompt helpers shared by the copilot providers."""

from __future__ import annotations

import json
from collections.abc import Sequence
from textwrap import dedent
from typing import Any

from app.core.redaction import redact_text
from app.integrations.copilot.base import CopilotContext


SYSTEM_PROMPT = dedent(
    """
    You are NexusAI Copilot, an evidence-first assistant for incident response.
    Rules:
    - Use only the provided context.
    - Be concise, direct, and operational.
    - If the question asks about cost and no cost data is present, say cost data is not connected yet and pivot to incident or health evidence.
    - Do not invent facts or speculate beyond the evidence.
    - Return valid JSON with keys: answer, confidence, follow_up, evidence.
    - evidence must be an array of 2 to 4 short strings.
    """
).strip()


def build_copilot_prompt(question: str, context: CopilotContext) -> str:
    """Build the shared prompt text used by live and local providers."""

    summary_block = "\n".join(f"- {line}" for line in context.summary_lines) or "- No summary data."
    evidence_block = "\n".join(f"- {line}" for line in context.evidence_lines) or "- No alert evidence is present yet."
    top_alert_block = (
        f"- {context.top_alert_severity.upper() if context.top_alert_severity else 'UNKNOWN'} {context.top_alert_scope}: {context.top_alert_title}"
        if context.top_alert_title and context.top_alert_scope
        else "- No top alert is available yet."
    )

    return dedent(
        f"""
        {SYSTEM_PROMPT}

        Context summary:
        {summary_block}

        Top alert:
        {top_alert_block}

        Evidence lines:
        {evidence_block}

        Question:
        {redact_text(question)}
        """
    ).strip()


def parse_structured_reply(raw_text: str, fallback_evidence: Sequence[str]) -> dict[str, Any]:
    """Parse a compact JSON reply or fall back to a safe plain-text shape."""

    candidate = raw_text.strip()
    payload: dict[str, Any] | None = None

    for value in (candidate, _extract_json_candidate(candidate)):
        if not value:
            continue
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            continue
        if isinstance(loaded, dict):
            payload = loaded
            break

    if payload is None:
        return {
            "answer": candidate or "I could not produce a structured answer.",
            "confidence": 0.58,
            "follow_up": "Which service should we inspect next?",
            "evidence": list(fallback_evidence)[:3],
        }

    answer = str(payload.get("answer") or candidate or "I could not produce a structured answer.")
    follow_up = str(payload.get("follow_up") or "Which service should we inspect next?")
    confidence = payload.get("confidence", 0.64)
    evidence = payload.get("evidence", list(fallback_evidence)[:3])
    if not isinstance(evidence, list):
        evidence = list(fallback_evidence)[:3]

    normalized_evidence = [str(item) for item in evidence if str(item).strip()][:4]
    if not normalized_evidence:
        normalized_evidence = list(fallback_evidence)[:3]

    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        confidence_value = 0.64

    return {
        "answer": answer,
        "confidence": max(0.0, min(1.0, round(confidence_value, 2))),
        "follow_up": follow_up,
        "evidence": normalized_evidence,
    }


def _extract_json_candidate(value: str) -> str | None:
    """Extract the first JSON-looking block from a response string."""

    start = value.find("{")
    end = value.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return value[start : end + 1]

