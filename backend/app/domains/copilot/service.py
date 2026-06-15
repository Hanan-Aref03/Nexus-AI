"""Copilot orchestration for the alerts and investigation workspace."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from app.core.auth import SecurityPrincipal
from app.core.guardrails import EvaluationScorecard, LocalGuardrailEngine, LocalRagasEvaluator
from app.core.redaction import redact_text
from app.domains.alerts.repositories import AlertsRepository
from app.domains.alerts.rules import build_alert_feed
from app.domains.alerts.schemas import AlertSummary
from app.domains.copilot.schemas import CopilotAnswerOut, CopilotEvaluationOut
from app.integrations.copilot import CopilotContext, CopilotProviderChain
from app.integrations.copilot.base import CopilotReply


class CopilotService:
    """Answer workspace questions from the tenant's current evidence."""

    def __init__(
        self,
        repository: AlertsRepository,
        provider_chain: CopilotProviderChain,
        guardrail_engine: LocalGuardrailEngine,
        evaluation_engine: LocalRagasEvaluator,
        *,
        max_context_items: int = 5,
    ) -> None:
        self._repository = repository
        self._provider_chain = provider_chain
        self._guardrail_engine = guardrail_engine
        self._evaluation_engine = evaluation_engine
        self._max_context_items = max_context_items

    def answer(self, principal: SecurityPrincipal, question: str) -> CopilotAnswerOut:
        """Return an evidence-backed answer for the current tenant."""

        findings = self._repository.list_findings(principal, limit=self._max_context_items)
        incidents = self._repository.list_incidents(principal, limit=self._max_context_items)
        health_scores = self._repository.list_health_scores(principal, limit=self._max_context_items)

        has_live_data = bool(findings or incidents or health_scores)
        feed = build_alert_feed(
            findings,
            incidents,
            health_scores,
            mode="live" if has_live_data else "demo",
            source_label="Live workspace analysis" if has_live_data else "Sample workspace snapshot",
            source_reason=(
                "The copilot is grounded in the current incidents and health scores for this tenant."
                if has_live_data
                else "No live analysis data is present yet, so a calm sample workspace is used instead."
            ),
        )
        summary = self._summarize_feed(feed.alerts)
        context = self._build_context(feed, summary)
        assessment = self._guardrail_engine.assess(
            question,
            context={
                "mode": feed.mode,
                "source_label": feed.source_label,
                "alert_count": len(feed.alerts),
                "tenant_id": principal.tenant_id,
            },
        )
        safe_question = assessment.sanitized_input

        if assessment.allowed:
            reply = self._provider_chain.answer(safe_question, context)
        else:
            reply = self._blocked_reply(context)

        scorecard = self._evaluate_reply(safe_question, reply)
        now = datetime.now(timezone.utc)
        top_alert = feed.alerts[0] if feed.alerts else None

        return CopilotAnswerOut(
            mode=feed.mode,
            generated_at=now,
            source_label=feed.source_label,
            source_reason=feed.source_reason,
            question=redact_text(question),
            provider=reply.provider,
            used_fallback=reply.used_fallback,
            answer=reply.answer,
            confidence=round(reply.confidence, 2),
            follow_up=reply.follow_up,
            evidence=reply.evidence,
            evaluation=CopilotEvaluationOut(
                policy=scorecard.policy,
                faithfulness=scorecard.faithfulness,
                answer_relevancy=scorecard.answer_relevancy,
                context_precision=scorecard.context_precision,
                summary=scorecard.summary,
            ),
            top_alert_title=top_alert.title if top_alert else None,
            top_alert_scope=top_alert.scope_name if top_alert else None,
            top_alert_severity=top_alert.severity.value if top_alert else None,
        )

    def _summarize_feed(self, alerts) -> AlertSummary:
        """Summarize the draft alert list for the copilot prompt context."""

        severities = Counter(alert.severity.value for alert in alerts)
        kinds = Counter(alert.kind for alert in alerts)
        security_count = sum(1 for alert in alerts if "security" in alert.tags)
        scopes = {
            (alert.scope_kind.value if hasattr(alert.scope_kind, "value") else str(alert.scope_kind), alert.scope_name)
            for alert in alerts
        }

        return AlertSummary(
            total=len(alerts),
            incidents=kinds.get("incident", 0),
            health=kinds.get("health", 0),
            security=security_count,
            critical=severities.get("critical", 0),
            warning=severities.get("warning", 0),
            info=severities.get("info", 0),
            scopes=len(scopes),
        )

    def _build_context(self, feed, summary: AlertSummary) -> CopilotContext:
        """Convert the current alert feed into a provider prompt context."""

        summary_lines = (
            f"{summary.total} alert(s): {summary.incidents} incident(s), {summary.health} health signal(s), {summary.security} security alert(s).",
            f"Source label: {feed.source_label}.",
            f"Source reason: {feed.source_reason}.",
        )
        evidence_lines = tuple(
            f"{alert.severity.value.upper()} {alert.kind} in {alert.scope_name}: {alert.title} - {alert.summary}"
            for alert in feed.alerts[: self._max_context_items]
        )
        top_alert = feed.alerts[0] if feed.alerts else None
        return CopilotContext(
            mode=feed.mode,
            source_label=feed.source_label,
            source_reason=feed.source_reason,
            summary_lines=summary_lines,
            evidence_lines=evidence_lines,
            top_alert_title=top_alert.title if top_alert else None,
            top_alert_scope=f"{top_alert.scope_kind.value} {top_alert.scope_name}" if top_alert else None,
            top_alert_severity=top_alert.severity.value if top_alert else None,
        )

    def _blocked_reply(self, context: CopilotContext) -> CopilotReply:
        """Return a safe answer when the question trips the local guardrail."""

        evidence = list(context.evidence_lines[:3])
        return CopilotReply(
            provider="guardrails",
            answer=(
                "I can help with incident and service-health questions, but I can't process that prompt as written. "
                "Please rephrase it without secrets or credentials, and I’ll ground the answer in the current evidence."
            ),
            confidence=0.0,
            follow_up="Which incident or service-health signal should we inspect next?",
            evidence=evidence or ["No active alerts are ready for delivery."],
            used_fallback=True,
        )

    def _evaluate_reply(self, question: str, reply: CopilotReply) -> EvaluationScorecard:
        """Run the local evaluation seam on the final answer."""

        context = reply.evidence or []
        return self._evaluation_engine.evaluate(
            prompt=question,
            response=reply.answer,
            context=context,
        )
