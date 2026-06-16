"""Copilot API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import SecurityPrincipal, emit_security_event, require_roles
from app.core.dependencies import get_session
from app.core.guardrails import LocalGuardrailEngine, LocalRagasEvaluator
from app.domains.alerts.repositories import AlertsRepository
from app.domains.copilot.schemas import CopilotAnswerOut, CopilotQuestionIn
from app.domains.copilot.service import CopilotService


copilot_router = APIRouter(prefix="/copilot", tags=["copilot"])


@copilot_router.post("/query", response_model=CopilotAnswerOut)
def ask_copilot(
    request: Request,
    payload: CopilotQuestionIn,
    session: Session = Depends(get_session),
    principal: SecurityPrincipal = Depends(require_roles("alerts:read", "analysis:read")),
) -> CopilotAnswerOut:
    """Answer an operational question from the current tenant's evidence."""

    service = CopilotService(
        AlertsRepository(session),
        request.app.state.copilot_provider_chain,
        request.app.state.guardrail_engine if hasattr(request.app.state, "guardrail_engine") else LocalGuardrailEngine(),
        request.app.state.evaluation_engine if hasattr(request.app.state, "evaluation_engine") else LocalRagasEvaluator(),
    )
    answer = service.answer(principal, payload.question)

    emit_security_event(
        request,
        action="copilot.query",
        outcome="blocked" if answer.provider == "guardrails" else "allowed",
        principal=principal,
        details={
            "provider": answer.provider,
            "used_fallback": answer.used_fallback,
            "question": payload.question,
        },
    )
    return answer

