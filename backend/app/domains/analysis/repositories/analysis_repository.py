"""Persistence helpers for the analysis domain."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.auth import SecurityPrincipal
from app.core.rls import apply_tenant_context
from app.domains.analysis.models import AnalysisEvaluationRecord, AnalysisFindingRecord, AnalysisIncidentRecord
from app.domains.telemetry.models import TelemetrySignalRecord


class AnalysisRepository:
    """Thin repository around the detection-core tables."""

    def __init__(self, session: Session):
        self._session = session

    def list_unprocessed_signals(self, principal: SecurityPrincipal, limit: int = 200) -> list[TelemetrySignalRecord]:
        """Return telemetry signals that have not been evaluated yet."""

        apply_tenant_context(self._session, principal)
        statement = (
            select(TelemetrySignalRecord)
            .outerjoin(
                AnalysisEvaluationRecord,
                (AnalysisEvaluationRecord.telemetry_signal_id == TelemetrySignalRecord.id)
                & (AnalysisEvaluationRecord.tenant_id == TelemetrySignalRecord.tenant_id),
            )
            .where(TelemetrySignalRecord.tenant_id == principal.tenant_id)
            .where(AnalysisEvaluationRecord.id.is_(None))
            .order_by(desc(TelemetrySignalRecord.observed_at), desc(TelemetrySignalRecord.received_at))
            .limit(limit)
        )
        return list(self._session.scalars(statement))

    def find_active_incident(self, principal: SecurityPrincipal, correlation_key: str) -> AnalysisIncidentRecord | None:
        """Return the latest non-resolved incident for a correlation group."""

        apply_tenant_context(self._session, principal)
        statement = (
            select(AnalysisIncidentRecord)
            .where(AnalysisIncidentRecord.tenant_id == principal.tenant_id)
            .where(AnalysisIncidentRecord.correlation_key == correlation_key)
            .where(AnalysisIncidentRecord.state != "resolved")
            .order_by(desc(AnalysisIncidentRecord.updated_at), desc(AnalysisIncidentRecord.created_at))
            .limit(1)
        )
        return self._session.scalars(statement).first()

    def get_incident(self, principal: SecurityPrincipal, incident_id: str) -> AnalysisIncidentRecord | None:
        """Fetch one incident by id within the current tenant."""

        apply_tenant_context(self._session, principal)
        statement = (
            select(AnalysisIncidentRecord)
            .where(AnalysisIncidentRecord.tenant_id == principal.tenant_id)
            .where(AnalysisIncidentRecord.id == incident_id)
            .limit(1)
        )
        return self._session.scalars(statement).first()

    def list_incidents(self, principal: SecurityPrincipal, limit: int = 50) -> list[AnalysisIncidentRecord]:
        """Return incidents ordered by the most recent activity."""

        apply_tenant_context(self._session, principal)
        statement = (
            select(AnalysisIncidentRecord)
            .where(AnalysisIncidentRecord.tenant_id == principal.tenant_id)
            .order_by(desc(AnalysisIncidentRecord.updated_at), desc(AnalysisIncidentRecord.created_at))
            .limit(limit)
        )
        return list(self._session.scalars(statement))

    def list_findings(self, principal: SecurityPrincipal, limit: int = 100) -> list[AnalysisFindingRecord]:
        """Return findings ordered by newest first."""

        apply_tenant_context(self._session, principal)
        statement = (
            select(AnalysisFindingRecord)
            .where(AnalysisFindingRecord.tenant_id == principal.tenant_id)
            .order_by(desc(AnalysisFindingRecord.created_at), desc(AnalysisFindingRecord.observed_at))
            .limit(limit)
        )
        return list(self._session.scalars(statement))

    def list_findings_for_incident(self, principal: SecurityPrincipal, incident_id: str) -> list[AnalysisFindingRecord]:
        """Return the evidence rows that belong to one incident."""

        apply_tenant_context(self._session, principal)
        statement = (
            select(AnalysisFindingRecord)
            .where(AnalysisFindingRecord.tenant_id == principal.tenant_id)
            .where(AnalysisFindingRecord.incident_id == incident_id)
            .order_by(desc(AnalysisFindingRecord.created_at), desc(AnalysisFindingRecord.observed_at))
        )
        return list(self._session.scalars(statement))

    def add_all(self, records: Sequence[object]) -> None:
        """Stage new ORM records for persistence."""

        self._session.add_all(list(records))

    def commit(self) -> None:
        """Commit the current unit of work."""

        self._session.commit()


__all__ = ["AnalysisRepository"]
