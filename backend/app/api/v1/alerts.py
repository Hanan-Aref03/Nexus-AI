"""Alerts API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import SecurityPrincipal, require_roles
from app.core.dependencies import get_session
from app.domains.alerts.repositories import AlertsRepository
from app.domains.alerts.schemas import AlertsFeedOut
from app.domains.alerts.services import AlertsService


alerts_router = APIRouter(prefix="/alerts", tags=["alerts"])


@alerts_router.get("", response_model=AlertsFeedOut)
def list_alerts(
    request: Request,
    session: Session = Depends(get_session),
    principal: SecurityPrincipal = Depends(require_roles("alerts:read")),
    limit: int = Query(default=12, ge=1, le=50),
) -> AlertsFeedOut:
    """Return the current workspace alert inbox."""

    slack_connector = getattr(request.app.state, "slack_connector", None)
    return AlertsService(AlertsRepository(session), slack_connector=slack_connector).list_alerts(
        principal=principal,
        limit=limit,
    )
