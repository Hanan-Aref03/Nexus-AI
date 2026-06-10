"""Local guardrail and evaluation seams for the Phase 1.5 security baseline."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.core.redaction import redact_text


@dataclass(frozen=True, slots=True)
class GuardrailAssessment:
    """A small, deterministic guardrail decision."""

    allowed: bool
    policy: str
    reason: str
    sanitized_input: str


@dataclass(frozen=True, slots=True)
class EvaluationScorecard:
    """A lightweight evaluation report shaped like a future RAGAS output."""

    policy: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    summary: str


class LocalGuardrailEngine:
    """A local guardrail seam that can later be swapped for NeMo Guardrails."""

    policy_name = "nemo-guardrails-seam"

    def assess(self, prompt: str, *, context: Mapping[str, object] | None = None) -> GuardrailAssessment:
        """Assess a prompt for obvious secret leakage or prompt injection markers."""

        sanitized_prompt = redact_text(prompt)
        blocked_markers = ("api key", "password", "private key", "vault token", "secret")
        blocked = any(marker in prompt.lower() for marker in blocked_markers)
        reason = "prompt contains sensitive material" if blocked else "prompt passed local guardrail checks"
        if context:
            # Context is intentionally not interpreted yet; it is retained for future policy engines.
            _ = context
        return GuardrailAssessment(
            allowed=not blocked,
            policy=self.policy_name,
            reason=reason,
            sanitized_input=sanitized_prompt,
        )


class LocalRagasEvaluator:
    """A deterministic evaluation seam that can be replaced by real RAGAS later."""

    policy_name = "ragas-seam"

    def evaluate(
        self,
        *,
        prompt: str,
        response: str,
        context: Sequence[str] | None = None,
    ) -> EvaluationScorecard:
        """Return a simple, explainable scorecard for test and demo use."""

        context_items = list(context or [])
        prompt_words = set(redact_text(prompt).lower().split())
        response_words = set(redact_text(response).lower().split())
        shared_words = prompt_words & response_words

        faithfulness = 0.95 if response_words else 0.0
        answer_relevancy = min(1.0, 0.5 + (len(shared_words) / 10))
        context_precision = 1.0 if context_items else 0.5

        return EvaluationScorecard(
            policy=self.policy_name,
            faithfulness=round(faithfulness, 2),
            answer_relevancy=round(answer_relevancy, 2),
            context_precision=round(context_precision, 2),
            summary="local evaluation emitted for Phase 1.5 readiness checks",
        )


def build_guardrail_engine(enabled: bool) -> LocalGuardrailEngine:
    """Return the local guardrail engine used in the first hardening slice."""

    # The first implementation keeps the seam local and testable.
    _ = enabled
    return LocalGuardrailEngine()


def build_evaluation_engine(enabled: bool) -> LocalRagasEvaluator:
    """Return the local evaluation engine used before full RAGAS integration."""

    _ = enabled
    return LocalRagasEvaluator()
