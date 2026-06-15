"""Pydantic schemas for the Phase 4 copilot endpoint."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CopilotQuestionIn(BaseModel):
    """User question sent from the workspace copilot UI."""

    question: str = Field(min_length=3, max_length=1000)


class CopilotEvaluationOut(BaseModel):
    """Lightweight evaluation output used to keep the assistant honest."""

    policy: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    summary: str


class CopilotAnswerOut(BaseModel):
    """Normalized answer returned to the frontend copilot panel."""

    model_config = ConfigDict(from_attributes=True)

    mode: str
    generated_at: datetime
    source_label: str
    source_reason: str
    question: str
    provider: str
    used_fallback: bool
    answer: str
    confidence: float
    follow_up: str
    evidence: list[str]
    evaluation: CopilotEvaluationOut
    top_alert_title: str | None
    top_alert_scope: str | None
    top_alert_severity: str | None

