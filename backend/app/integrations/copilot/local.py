"""Local copilot implementation used when no live provider is configured."""

from __future__ import annotations

from app.integrations.copilot.base import CopilotContext, CopilotProvider, CopilotReply


class LocalCopilotProvider(CopilotProvider):
    """Answer questions from the already loaded workspace evidence."""

    provider_name = "local"

    def answer(self, question: str, context: CopilotContext) -> CopilotReply:
        """Return a deterministic, evidence-backed answer."""

        lower_question = question.lower()
        evidence = list(context.evidence_lines[:3])

        if not evidence:
            return CopilotReply(
                provider=self.provider_name,
                answer="The workspace is calm right now, and there is no active incident evidence to expand yet.",
                confidence=0.42,
                follow_up="Which service should we inspect next?",
                evidence=["No active alerts are ready for delivery."],
            )

        if "cost" in lower_question:
            answer = (
                "Cost telemetry is not connected in this phase yet, so I can only answer from incident and health evidence. "
                f"The strongest signal is {evidence[0]}."
            )
            follow_up = "Which incident or service-health signal should we inspect next?"
            confidence = 0.54
        elif "security" in lower_question or (context.top_alert_severity or "").lower() == "critical":
            answer = (
                "The strongest security lead is the current critical evidence in the workspace. "
                f"{evidence[0]} should be reviewed first."
            )
            follow_up = "Do you want me to expand the incident evidence or the service-health trail?"
            confidence = 0.86
        elif "health" in lower_question or "service" in lower_question:
            answer = (
                "The current service-health picture is driven by the active alert queue. "
                f"{evidence[0]} is the clearest place to start."
            )
            follow_up = "Which service do you want to inspect in more detail?"
            confidence = 0.79
        else:
            answer = (
                "The current response queue is anchored by the top alert and its supporting evidence. "
                f"{evidence[0]} is the best next review point."
            )
            follow_up = "What follow-up question should I answer next?"
            confidence = 0.74

        return CopilotReply(
            provider=self.provider_name,
            answer=answer,
            confidence=confidence,
            follow_up=follow_up,
            evidence=evidence,
        )

