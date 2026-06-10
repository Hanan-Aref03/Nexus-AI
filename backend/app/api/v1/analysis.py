"""Detection-core routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import SecurityPrincipal, require_roles
from app.core.dependencies import get_session
from app.domains.analysis.repositories import AnalysisRepository
from app.domains.analysis.schemas import (
    AnalysisFindingOut,
    AnalysisHealthScore,
    AnalysisIncidentOut,
    AnalysisIncidentState,
    AnalysisIncidentUpdateRequest,
    AnalysisRunResult,
)
from app.domains.analysis.services import AnalysisService


analysis_router = APIRouter(prefix="/analysis", tags=["analysis"])


def _build_service(session: Session) -> AnalysisService:
    """Create the analysis service around the request-scoped session."""

    return AnalysisService(AnalysisRepository(session))


@analysis_router.post("/run", response_model=AnalysisRunResult)
def run_analysis(
    session: Session = Depends(get_session),
    principal: SecurityPrincipal = Depends(require_roles("analysis:write")),
    limit: int = Query(default=200, ge=1, le=1000),
) -> AnalysisRunResult:
    """Evaluate any new telemetry and persist the resulting analysis output."""

    return _build_service(session).analyze(principal=principal, limit=limit)


@analysis_router.get("/findings", response_model=list[AnalysisFindingOut])
def list_findings(
    session: Session = Depends(get_session),
    principal: SecurityPrincipal = Depends(require_roles("analysis:read")),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AnalysisFindingOut]:
    """Return the most recent detection findings."""

    return _build_service(session).list_findings(principal=principal, limit=limit)


@analysis_router.get("/incidents", response_model=list[AnalysisIncidentOut])
def list_incidents(
    session: Session = Depends(get_session),
    principal: SecurityPrincipal = Depends(require_roles("analysis:read")),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AnalysisIncidentOut]:
    """Return the current incident list with attached evidence."""

    return _build_service(session).list_incidents(principal=principal, limit=limit)


@analysis_router.get("/incidents/{incident_id}", response_model=AnalysisIncidentOut)
def get_incident(
    incident_id: str,
    session: Session = Depends(get_session),
    principal: SecurityPrincipal = Depends(require_roles("analysis:read")),
) -> AnalysisIncidentOut:
    """Return a single incident with its evidence payload."""

    incident = _build_service(session).get_incident(principal=principal, incident_id=incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return incident


@analysis_router.patch("/incidents/{incident_id}", response_model=AnalysisIncidentOut)
def update_incident_state(
    incident_id: str,
    payload: AnalysisIncidentUpdateRequest,
    session: Session = Depends(get_session),
    principal: SecurityPrincipal = Depends(require_roles("analysis:write")),
) -> AnalysisIncidentOut:
    """Move an incident through the supported lifecycle states."""

    incident = _build_service(session).update_incident_state(
        principal=principal,
        incident_id=incident_id,
        state=AnalysisIncidentState(payload.state),
    )
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return incident


@analysis_router.get("/health-scores", response_model=list[AnalysisHealthScore])
def health_scores(
    session: Session = Depends(get_session),
    principal: SecurityPrincipal = Depends(require_roles("analysis:read")),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AnalysisHealthScore]:
    """Return service and workload health scores for the current tenant."""

    return _build_service(session).list_health_scores(principal=principal, limit=limit)

