"""Pydantic schemas for the Phase 5 FinOps surface."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.domains.analysis.schemas import AnalysisScopeKind


class FinOpsOpportunityKind(str, Enum):
    """Kinds of savings opportunities surfaced by the FinOps lens."""

    rightsizing = "rightsizing"
    idle_resource = "idle_resource"
    efficiency = "efficiency"
    reliability = "reliability"


class FinOpsForecastKind(str, Enum):
    """Kinds of predictive reliability forecasts."""

    storage = "storage"
    saturation = "saturation"
    traffic = "traffic"
    reliability = "reliability"


class FinOpsOpportunityOut(BaseModel):
    """A single cost-saving or waste-reduction opportunity."""

    model_config = ConfigDict(from_attributes=True)

    kind: FinOpsOpportunityKind
    scope_kind: AnalysisScopeKind
    scope_name: str
    headline: str
    summary: str
    estimated_monthly_savings: float
    confidence: float
    risk_level: str
    evidence: list[str]
    recommendations: list[str]
    horizon_days: int


class FinOpsForecastOut(BaseModel):
    """A single forecast that warns about capacity or reliability risk."""

    model_config = ConfigDict(from_attributes=True)

    kind: FinOpsForecastKind
    scope_kind: AnalysisScopeKind | None
    scope_name: str | None
    headline: str
    summary: str
    horizon_days: int
    confidence: float
    risk_level: str
    evidence: list[str]
    recommendations: list[str]


class FinOpsInsightsOut(BaseModel):
    """Workspace-level FinOps and predictive reliability summary."""

    mode: str
    generated_at: datetime
    source_label: str
    source_reason: str
    estimated_monthly_savings: float
    risk_score: int
    opportunity_count: int
    forecast_count: int
    opportunities: list[FinOpsOpportunityOut]
    forecasts: list[FinOpsForecastOut]
    recommendations: list[str]
    top_scope: str | None
