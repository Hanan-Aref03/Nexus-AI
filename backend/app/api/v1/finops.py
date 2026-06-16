"""FinOps and predictive reliability routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import SecurityPrincipal, emit_security_event, require_roles
from app.core.dependencies import get_session
from app.domains.analysis.repositories import AnalysisRepository
from app.domains.finops.schemas import FinOpsInsightsOut
from app.domains.finops.service import FinOpsService


finops_router = APIRouter(prefix="/finops", tags=["finops"])


@finops_router.get("/insights", response_model=FinOpsInsightsOut)
def list_finops_insights(
    request: Request,
    session: Session = Depends(get_session),
    principal: SecurityPrincipal = Depends(require_roles("analysis:read")),
    limit: int = Query(default=100, ge=1, le=500),
) -> FinOpsInsightsOut:
    """Return the workspace's current cost and reliability foresight."""

    insights = FinOpsService(AnalysisRepository(session)).summarize(principal=principal, limit=limit)
    emit_security_event(
        request,
        action="finops.insights",
        outcome="allowed",
        principal=principal,
        details={
            "estimated_monthly_savings": insights.estimated_monthly_savings,
            "risk_score": insights.risk_score,
            "opportunity_count": insights.opportunity_count,
            "forecast_count": insights.forecast_count,
        },
    )
    return insights
