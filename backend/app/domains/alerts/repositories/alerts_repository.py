"""Read-only access helpers for the alerts feed."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.auth import SecurityPrincipal
from app.domains.analysis.repositories import AnalysisRepository
from app.domains.analysis.rules import calculate_health_scores
from app.domains.analysis.schemas import AnalysisHealthScore


class AlertsRepository:
    """Expose the existing analysis data through an alerts-specific seam."""

    def __init__(self, session: Session):
        self._analysis_repository = AnalysisRepository(session)

    def list_findings(self, principal: SecurityPrincipal, limit: int = 100):
        """Return the latest findings for alert derivation."""

        return self._analysis_repository.list_findings(principal, limit=limit)

    def list_incidents(self, principal: SecurityPrincipal, limit: int = 50):
        """Return the latest incidents for alert derivation."""

        return self._analysis_repository.list_incidents(principal, limit=limit)

    def list_health_scores(self, principal: SecurityPrincipal, limit: int = 100) -> list[AnalysisHealthScore]:
        """Compute the current health signal for the tenant."""

        findings = self._analysis_repository.list_findings(principal, limit=limit)
        incidents = self._analysis_repository.list_incidents(principal, limit=limit)
        return calculate_health_scores(findings, incidents)

