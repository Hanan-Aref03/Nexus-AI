"""FinOps and predictive reliability orchestration for the final phase."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

from app.core.auth import SecurityPrincipal
from app.domains.analysis.repositories import AnalysisRepository
from app.domains.analysis.rules import calculate_health_scores
from app.domains.analysis.schemas import AnalysisHealthScore
from app.domains.finops.schemas import (
    FinOpsForecastKind,
    FinOpsForecastOut,
    FinOpsInsightsOut,
    FinOpsOpportunityKind,
    FinOpsOpportunityOut,
)


class FinOpsService:
    """Derive savings opportunities and predictive reliability signals from analysis output."""

    def __init__(self, repository: AnalysisRepository):
        self._repository = repository

    def summarize(self, principal: SecurityPrincipal, limit: int = 100) -> FinOpsInsightsOut:
        """Return workspace-level FinOps guidance for the current tenant."""

        findings = self._repository.list_findings(principal, limit=limit)
        incidents = self._repository.list_incidents(principal, limit=limit)
        health_scores = calculate_health_scores(findings, incidents)
        if not findings and not incidents and not health_scores:
            return self._demo_insights()

        opportunities = self._build_opportunities(findings, incidents, health_scores)
        forecasts = self._build_forecasts(findings, incidents, health_scores)
        estimated_monthly_savings = round(sum(item.estimated_monthly_savings for item in opportunities), 2)
        risk_score = self._risk_score(findings, incidents, health_scores)
        recommendations = self._combine_recommendations(opportunities, forecasts)
        top_scope = opportunities[0].scope_name if opportunities else self._top_scope_name(health_scores)
        has_live_data = bool(findings or incidents or health_scores)

        return FinOpsInsightsOut(
            mode="live" if has_live_data else "demo",
            generated_at=datetime.now(timezone.utc),
            source_label="Live workspace analysis" if has_live_data else "Sample workspace scenario",
            source_reason=(
                "The FinOps lens is derived from the current analysis store, so savings and risk stay evidence-backed."
                if has_live_data
                else "No live analysis state is present yet, so a calm sample scenario keeps the final workspace useful."
            ),
            estimated_monthly_savings=estimated_monthly_savings,
            risk_score=risk_score,
            opportunity_count=len(opportunities),
            forecast_count=len(forecasts),
            opportunities=opportunities,
            forecasts=forecasts,
            recommendations=recommendations,
            top_scope=top_scope,
        )

    def _build_opportunities(
        self,
        findings: list[object],
        incidents: list[object],
        health_scores: list[AnalysisHealthScore],
    ) -> list[FinOpsOpportunityOut]:
        """Turn grouped signals into the most actionable savings opportunities."""

        health_index = {
            (score.scope_kind.value if hasattr(score.scope_kind, "value") else str(score.scope_kind), score.scope_name): score
            for score in health_scores
        }
        incident_index = defaultdict(list)
        for incident in incidents:
            incident_index[self._scope_key(incident)].append(incident)

        buckets: dict[tuple[str, str], list[object]] = defaultdict(list)
        for finding in findings:
            buckets[self._scope_key(finding)].append(finding)

        opportunities: list[FinOpsOpportunityOut] = []
        for (scope_kind, scope_name), scope_findings in buckets.items():
            health = health_index.get((scope_kind, scope_name))
            scope_incidents = incident_index.get((scope_kind, scope_name), [])
            opportunity = self._build_opportunity(scope_kind, scope_name, scope_findings, scope_incidents, health)
            if opportunity is not None:
                opportunities.append(opportunity)

        opportunities.sort(key=lambda item: (item.estimated_monthly_savings, item.confidence), reverse=True)
        return opportunities[:5]

    def _build_opportunity(
        self,
        scope_kind: str,
        scope_name: str,
        findings: list[object],
        incidents: list[object],
        health: AnalysisHealthScore | None,
    ) -> FinOpsOpportunityOut | None:
        """Build one savings opportunity from a scope bucket."""

        categories = Counter(str(getattr(finding, "category", "")) for finding in findings)
        if not categories and not health and not incidents:
            return None

        capacity_count = categories.get("capacity", 0)
        performance_count = categories.get("performance", 0)
        reliability_count = categories.get("reliability", 0)
        open_incidents = sum(1 for incident in incidents if str(getattr(incident, "state", "")) != "resolved")

        if not capacity_count and not performance_count and not reliability_count and (health is None or health.score >= 95) and open_incidents == 0:
            return None

        estimated_monthly_savings = 0.0
        if capacity_count:
            estimated_monthly_savings += 120.0 + (capacity_count - 1) * 40.0
        if performance_count:
            estimated_monthly_savings += 60.0 + (performance_count - 1) * 20.0
        if reliability_count:
            estimated_monthly_savings += 45.0 + (reliability_count - 1) * 15.0
        if health is not None and health.status.value in {"watch", "degraded", "critical"}:
            estimated_monthly_savings += max(0.0, (100 - health.score) * 1.75)
        if open_incidents:
            estimated_monthly_savings += open_incidents * 35.0

        estimated_monthly_savings = round(min(estimated_monthly_savings, 950.0), 2)
        confidence = round(
            min(
                0.96,
                0.52
                + (0.08 * min(len(findings), 4))
                + (0.05 if capacity_count else 0.0)
                + (0.04 if performance_count else 0.0)
                + (0.04 if health is not None and health.status.value in {"degraded", "critical"} else 0.0),
            ),
            2,
        )
        risk_level = self._risk_level(health, open_incidents, capacity_count, performance_count, reliability_count)
        horizon_days = self._horizon_days(health, capacity_count, performance_count, reliability_count, open_incidents)
        headline = self._opportunity_headline(scope_name, capacity_count, performance_count, reliability_count)
        summary = self._opportunity_summary(scope_name, findings, health, open_incidents)
        evidence = self._opportunity_evidence(findings, health, incidents)
        recommendations = self._opportunity_recommendations(scope_name, capacity_count, performance_count, reliability_count, health)

        return FinOpsOpportunityOut(
            kind=self._opportunity_kind(capacity_count, performance_count, reliability_count, health),
            scope_kind=self._normalize_scope_kind(scope_kind),
            scope_name=scope_name,
            headline=headline,
            summary=summary,
            estimated_monthly_savings=estimated_monthly_savings,
            confidence=confidence,
            risk_level=risk_level,
            evidence=evidence,
            recommendations=recommendations,
            horizon_days=horizon_days,
        )

    def _build_forecasts(
        self,
        findings: list[object],
        incidents: list[object],
        health_scores: list[AnalysisHealthScore],
    ) -> list[FinOpsForecastOut]:
        """Convert current pressure signals into conservative forecasts."""

        forecasts: list[FinOpsForecastOut] = []
        health_by_scope = {
            (score.scope_kind.value if hasattr(score.scope_kind, "value") else str(score.scope_kind), score.scope_name): score
            for score in health_scores
        }
        findings_by_scope: dict[tuple[str, str], list[object]] = defaultdict(list)
        incidents_by_scope: dict[tuple[str, str], list[object]] = defaultdict(list)

        for finding in findings:
            findings_by_scope[self._scope_key(finding)].append(finding)
        for incident in incidents:
            incidents_by_scope[self._scope_key(incident)].append(incident)

        for (scope_kind, scope_name), scope_findings in findings_by_scope.items():
            health = health_by_scope.get((scope_kind, scope_name))
            scope_incidents = incidents_by_scope.get((scope_kind, scope_name), [])
            capacity_count = sum(1 for finding in scope_findings if str(getattr(finding, "category", "")) == "capacity")
            performance_count = sum(1 for finding in scope_findings if str(getattr(finding, "category", "")) == "performance")
            reliability_count = sum(1 for finding in scope_findings if str(getattr(finding, "category", "")) == "reliability")
            open_incidents = sum(1 for incident in scope_incidents if str(getattr(incident, "state", "")) != "resolved")

            if capacity_count or (health is not None and health.status.value in {"watch", "degraded", "critical"}):
                forecasts.append(
                    self._build_forecast(
                        kind=FinOpsForecastKind.saturation,
                        scope_kind=scope_kind,
                        scope_name=scope_name,
                        scope_findings=scope_findings,
                        health=health,
                        open_incidents=open_incidents,
                        pressure_score=capacity_count + performance_count,
                    )
                )

            if any(self._looks_like_storage(finding) for finding in scope_findings):
                forecasts.append(
                    self._build_forecast(
                        kind=FinOpsForecastKind.storage,
                        scope_kind=scope_kind,
                        scope_name=scope_name,
                        scope_findings=scope_findings,
                        health=health,
                        open_incidents=open_incidents,
                        pressure_score=max(1, capacity_count),
                    )
                )

            if performance_count:
                forecasts.append(
                    self._build_forecast(
                        kind=FinOpsForecastKind.traffic,
                        scope_kind=scope_kind,
                        scope_name=scope_name,
                        scope_findings=scope_findings,
                        health=health,
                        open_incidents=open_incidents,
                        pressure_score=performance_count,
                    )
                )

            if reliability_count or open_incidents:
                forecasts.append(
                    self._build_forecast(
                        kind=FinOpsForecastKind.reliability,
                        scope_kind=scope_kind,
                        scope_name=scope_name,
                        scope_findings=scope_findings,
                        health=health,
                        open_incidents=open_incidents,
                        pressure_score=reliability_count + open_incidents,
                    )
                )

        if not forecasts:
            forecasts.append(self._fallback_forecast(findings, incidents, health_scores))

        forecasts.sort(key=lambda item: (item.horizon_days, -item.confidence))
        return forecasts[:4]

    def _build_forecast(
        self,
        *,
        kind: FinOpsForecastKind,
        scope_kind: str,
        scope_name: str,
        scope_findings: list[object],
        health: AnalysisHealthScore | None,
        open_incidents: int,
        pressure_score: int,
    ) -> FinOpsForecastOut:
        """Build one risk forecast for a scope."""

        scope_findings = list(scope_findings)
        top_findings = scope_findings[:2]
        evidence = [str(getattr(finding, "title", "Unknown finding")) for finding in top_findings]
        if health is not None:
            evidence.append(health.primary_reason)

        horizon_days = self._forecast_horizon(kind, health, open_incidents, pressure_score)
        risk_level = "high" if horizon_days <= 14 else "elevated" if horizon_days <= 28 else "watch"
        confidence = round(
            min(
                0.95,
                0.56
                + (0.05 * min(len(scope_findings), 3))
                + (0.05 if health is not None and health.status.value in {"degraded", "critical"} else 0.0)
                + (0.04 if open_incidents else 0.0),
            ),
            2,
        )
        headline, summary, recommendations = self._forecast_text(kind, scope_name, health, open_incidents, pressure_score)

        return FinOpsForecastOut(
            kind=kind,
            scope_kind=self._normalize_scope_kind(scope_kind),
            scope_name=scope_name,
            headline=headline,
            summary=summary,
            horizon_days=horizon_days,
            confidence=confidence,
            risk_level=risk_level,
            evidence=self._unique_text(evidence),
            recommendations=recommendations,
        )

    def _risk_score(self, findings: list[object], incidents: list[object], health_scores: list[AnalysisHealthScore]) -> int:
        """Compute a conservative workspace risk score."""

        critical = sum(1 for score in health_scores if score.status.value == "critical")
        degraded = sum(1 for score in health_scores if score.status.value == "degraded")
        watch = sum(1 for score in health_scores if score.status.value == "watch")
        open_incidents = sum(1 for incident in incidents if str(getattr(incident, "state", "")) != "resolved")
        capacity_findings = sum(1 for finding in findings if str(getattr(finding, "category", "")) == "capacity")
        performance_findings = sum(1 for finding in findings if str(getattr(finding, "category", "")) == "performance")
        reliability_findings = sum(1 for finding in findings if str(getattr(finding, "category", "")) == "reliability")

        score = 18
        score += critical * 16
        score += degraded * 10
        score += watch * 6
        score += open_incidents * 9
        score += capacity_findings * 5
        score += performance_findings * 3
        score += reliability_findings * 4
        return min(score, 100)

    def _combine_recommendations(
        self,
        opportunities: list[FinOpsOpportunityOut],
        forecasts: list[FinOpsForecastOut],
    ) -> list[str]:
        """Merge the best next actions from opportunities and forecasts."""

        recommendations: list[str] = []
        for item in [*opportunities[:3], *forecasts[:3]]:
            recommendations.extend(item.recommendations[:2])
        return self._unique_text(recommendations)[:6]

    def _opportunity_kind(
        self,
        capacity_count: int,
        performance_count: int,
        reliability_count: int,
        health: AnalysisHealthScore | None,
    ) -> FinOpsOpportunityKind:
        """Pick the most appropriate kind for one opportunity."""

        if capacity_count and (health is None or health.status.value in {"watch", "degraded", "critical"}):
            return FinOpsOpportunityKind.rightsizing
        if capacity_count:
            return FinOpsOpportunityKind.idle_resource
        if performance_count:
            return FinOpsOpportunityKind.efficiency
        return FinOpsOpportunityKind.reliability if reliability_count or (health is not None and health.status.value == "critical") else FinOpsOpportunityKind.efficiency

    def _opportunity_headline(self, scope_name: str, capacity_count: int, performance_count: int, reliability_count: int) -> str:
        """Create a short headline for a savings opportunity."""

        if capacity_count:
            return f"{scope_name} can be right-sized"
        if performance_count:
            return f"{scope_name} is spending headroom on latency"
        if reliability_count:
            return f"{scope_name} needs a reliability budget check"
        return f"{scope_name} has a cost efficiency opportunity"

    def _opportunity_summary(
        self,
        scope_name: str,
        findings: list[object],
        health: AnalysisHealthScore | None,
        open_incidents: int,
    ) -> str:
        """Write a concise explanation for the savings opportunity."""

        categories = Counter(str(getattr(finding, "category", "")) for finding in findings)
        parts = [f"{scope_name} has {len(findings)} correlated finding(s)."]
        if categories.get("capacity"):
            parts.append(f"{categories['capacity']} capacity signal(s) suggest unused headroom or oversized requests.")
        if categories.get("performance"):
            parts.append(f"{categories['performance']} performance signal(s) indicate extra spend on latency or scaling pressure.")
        if health is not None:
            parts.append(f"Health is {health.score}/100, which keeps the opportunity evidence-backed.")
        if open_incidents:
            parts.append(f"{open_incidents} unresolved incident(s) are still amplifying the waste signal.")
        return " ".join(parts)

    def _opportunity_evidence(
        self,
        findings: list[object],
        health: AnalysisHealthScore | None,
        incidents: list[object],
    ) -> list[str]:
        """Collect a small evidence list for the opportunity card."""

        evidence = [str(getattr(finding, "title", "Unknown finding")) for finding in findings[:2]]
        if health is not None:
            evidence.append(health.primary_reason)
        evidence.extend(str(getattr(incident, "title", "Unknown incident")) for incident in incidents[:1])
        return self._unique_text(evidence)[:4]

    def _opportunity_recommendations(
        self,
        scope_name: str,
        capacity_count: int,
        performance_count: int,
        reliability_count: int,
        health: AnalysisHealthScore | None,
    ) -> list[str]:
        """Return concrete action lines for the opportunity card."""

        recommendations = []
        if capacity_count:
            recommendations.append(f"Right-size the requests or limits for {scope_name}.")
            recommendations.append("Validate that the observed headroom is not hiding a bursty workload.")
        if performance_count:
            recommendations.append(f"Reduce the hot-path latency for {scope_name} before autoscaling waste grows.")
            recommendations.append("Check traces, caching, and downstream dependencies.")
        if reliability_count or (health is not None and health.status.value == "critical"):
            recommendations.append("Treat the remaining reliability risk as a budget issue, not just an SRE issue.")
            recommendations.append("Keep one eye on error budgets while you tune the resource footprint.")
        if not recommendations:
            recommendations.append(f"Review {scope_name} and compare current usage against the expected baseline.")
        return self._unique_text(recommendations)[:3]

    def _risk_level(
        self,
        health: AnalysisHealthScore | None,
        open_incidents: int,
        capacity_count: int,
        performance_count: int,
        reliability_count: int,
    ) -> str:
        """Pick a human-readable severity for the opportunity."""

        score = health.score if health is not None else 100
        if score < 65 or open_incidents >= 2 or reliability_count >= 2:
            return "high"
        if score < 82 or capacity_count + performance_count >= 2 or open_incidents == 1:
            return "elevated"
        return "watch"

    def _horizon_days(
        self,
        health: AnalysisHealthScore | None,
        capacity_count: int,
        performance_count: int,
        reliability_count: int,
        open_incidents: int,
    ) -> int:
        """Estimate how quickly the opportunity becomes user-visible."""

        score = health.score if health is not None else 90
        horizon = 60
        horizon -= max(0, 100 - score) // 3
        horizon -= capacity_count * 6
        horizon -= performance_count * 4
        horizon -= reliability_count * 3
        horizon -= open_incidents * 5
        return max(7, min(horizon, 60))

    def _forecast_horizon(
        self,
        kind: FinOpsForecastKind,
        health: AnalysisHealthScore | None,
        open_incidents: int,
        pressure_score: int,
    ) -> int:
        """Estimate when the forecasted condition will matter."""

        score = health.score if health is not None else 90
        if kind == FinOpsForecastKind.storage:
            horizon = 30 - pressure_score * 4 - max(0, 85 - score) // 4
        elif kind == FinOpsForecastKind.saturation:
            horizon = 28 - pressure_score * 3 - max(0, 90 - score) // 5
        elif kind == FinOpsForecastKind.traffic:
            horizon = 35 - pressure_score * 4 - open_incidents * 2
        else:
            horizon = 24 - pressure_score * 4 - open_incidents * 3 - max(0, 80 - score) // 4
        return max(7, min(horizon, 60))

    def _forecast_text(
        self,
        kind: FinOpsForecastKind,
        scope_name: str,
        health: AnalysisHealthScore | None,
        open_incidents: int,
        pressure_score: int,
    ) -> tuple[str, str, list[str]]:
        """Build a short narrative for one forecast."""

        if kind == FinOpsForecastKind.storage:
            headline = f"{scope_name} storage could become the next bottleneck"
            summary = f"Capacity signals on {scope_name} point to storage or memory pressure if the trend keeps climbing."
            recommendations = [
                "Trim retention or scale the storage-heavy path before the line bends upward again.",
                "Set a tighter watch on disk or memory growth so the next threshold is visible earlier.",
            ]
        elif kind == FinOpsForecastKind.saturation:
            headline = f"{scope_name} is trending toward saturation"
            summary = f"Current pressure on {scope_name} suggests that resource headroom is shrinking."
            recommendations = [
                "Validate request and limit settings against actual usage.",
                "Reserve a little headroom before the next traffic spike arrives.",
            ]
        elif kind == FinOpsForecastKind.traffic:
            headline = f"{scope_name} traffic growth may drive avoidable spend"
            summary = f"Performance signals on {scope_name} imply the autoscaling or caching strategy should be revisited."
            recommendations = [
                "Check the hot path for caching, batching, or retry amplification opportunities.",
                "Compare current request growth against the expected baseline and tune alerts accordingly.",
            ]
        else:
            headline = f"{scope_name} reliability risk is still active"
            summary = f"Open incidents on {scope_name} are still consuming budget that should go to stability work."
            recommendations = [
                "Treat the remaining incident risk as a reliability investment decision.",
                "Review the dependency chain and the error budget before the next release.",
            ]

        if health is not None:
            summary = f"{summary} The current health score is {health.score}/100."
        if open_incidents:
            summary = f"{summary} {open_incidents} incident(s) are still open."
        if pressure_score > 1:
            summary = f"{summary} There are {pressure_score} pressure signal(s) in the same scope."

        return headline, summary, recommendations

    def _fallback_forecast(
        self,
        findings: list[object],
        incidents: list[object],
        health_scores: list[AnalysisHealthScore],
    ) -> FinOpsForecastOut:
        """Return a calm live forecast when the workspace has no immediate pressure."""

        top_scope = self._top_scope_name(health_scores)
        if top_scope is None and findings:
            _, top_scope = self._scope_pair(findings[0])
        if top_scope is None:
            top_scope = "workspace"

        scope_kind = "service"
        if findings:
            scope_kind, _ = self._scope_pair(findings[0])
        if top_scope == "workspace":
            scope_kind = "service"

        evidence = [str(getattr(finding, "title", "Unknown finding")) for finding in findings[:2]]
        if health_scores:
            evidence.append(sorted(health_scores, key=lambda score: score.score)[0].primary_reason)
        evidence.extend(str(getattr(incident, "title", "Unknown incident")) for incident in incidents[:1])

        return FinOpsForecastOut(
            kind=FinOpsForecastKind.reliability,
            scope_kind=self._normalize_scope_kind(scope_kind),
            scope_name=top_scope,
            headline=f"{top_scope} reliability should stay under watch",
            summary="The current workspace does not show an immediate FinOps forecast yet, but the final phase keeps a conservative reliability check in place.",
            horizon_days=42,
            confidence=0.66,
            risk_level="watch",
            evidence=self._unique_text(evidence)[:3] or ["No live evidence is present yet."],
            recommendations=[
                "Keep a small reliability reserve in the busiest scope.",
                "Review the next few telemetry batches before assuming the trend is flat.",
            ],
        )

    def _looks_like_storage(self, finding: object) -> bool:
        """Detect storage-oriented capacity pressure from a finding summary or title."""

        text = " ".join(str(getattr(finding, field, "") or "") for field in ("title", "summary")).lower()
        return any(keyword in text for keyword in ("disk", "storage", "volume", "filesystem", "retention"))

    def _scope_key(self, item: object) -> tuple[str, str]:
        """Pick a stable scope key from a finding or incident record."""

        scope_kind, scope_name = self._scope_pair(item)
        return scope_kind, scope_name

    def _scope_pair(self, item: object) -> tuple[str, str]:
        """Prefer the most actionable scope name while keeping the scope kind consistent."""

        for scope_kind in ("service", "workload", "cluster", "namespace"):
            value = getattr(item, f"{scope_kind}_name", None)
            if value:
                return scope_kind, str(value)
        return "service", str(getattr(item, "scope_name", None) or getattr(item, "source_name", None) or "workspace")

    def _normalize_scope_kind(self, value: str) -> "AnalysisScopeKind":
        """Return a scope kind that matches the API schema."""

        from app.domains.analysis.schemas import AnalysisScopeKind

        return AnalysisScopeKind(value)

    def _top_scope_name(self, health_scores: list[AnalysisHealthScore]) -> str | None:
        """Return the most strained scope name when no opportunity is available."""

        if not health_scores:
            return None
        return sorted(health_scores, key=lambda score: score.score)[0].scope_name

    def _unique_text(self, values: list[str]) -> list[str]:
        """Return deduplicated, non-empty text values in order."""

        unique: list[str] = []
        for value in values:
            text = str(value).strip()
            if text and text not in unique:
                unique.append(text)
        return unique

    def _demo_insights(self) -> FinOpsInsightsOut:
        """Return a calm sample scenario for a tenant without live analysis data."""

        return FinOpsInsightsOut(
            mode="demo",
            generated_at=datetime.now(timezone.utc),
            source_label="Sample workspace scenario",
            source_reason="No live analysis data is present yet, so a sample FinOps scenario keeps the final workspace useful.",
            estimated_monthly_savings=284.0,
            risk_score=58,
            opportunity_count=2,
            forecast_count=3,
            opportunities=[
                FinOpsOpportunityOut(
                    kind=FinOpsOpportunityKind.rightsizing,
                    scope_kind=self._normalize_scope_kind("cluster"),
                    scope_name="payments-prod",
                    headline="payments-prod can be right-sized",
                    summary="The sample scenario shows repeated capacity pressure and one unresolved incident on the main production cluster.",
                    estimated_monthly_savings=164.0,
                    confidence=0.88,
                    risk_level="elevated",
                    evidence=["Sample capacity trend", "Sample health score at 72/100"],
                    recommendations=[
                        "Reduce the requests or limits on the hot path.",
                        "Confirm whether the observed headroom is intentional.",
                    ],
                    horizon_days=18,
                ),
                FinOpsOpportunityOut(
                    kind=FinOpsOpportunityKind.efficiency,
                    scope_kind=self._normalize_scope_kind("service"),
                    scope_name="auth-api",
                    headline="auth-api is spending headroom on latency",
                    summary="The sample scenario also shows a latency-heavy service where caching or batching could reduce spend.",
                    estimated_monthly_savings=120.0,
                    confidence=0.82,
                    risk_level="watch",
                    evidence=["Sample performance trend", "Sample alert queue"],
                    recommendations=[
                        "Trim the hot path and review the downstream dependencies.",
                        "Compare the current traffic pattern against the expected baseline.",
                    ],
                    horizon_days=26,
                ),
            ],
            forecasts=[
                FinOpsForecastOut(
                    kind=FinOpsForecastKind.saturation,
                    scope_kind=self._normalize_scope_kind("cluster"),
                    scope_name="payments-prod",
                    headline="payments-prod is trending toward saturation",
                    summary="The sample scenario suggests the main cluster should keep a little more headroom before the next spike arrives.",
                    horizon_days=12,
                    confidence=0.86,
                    risk_level="high",
                    evidence=["Sample capacity trend", "Sample health score at 72/100"],
                    recommendations=[
                        "Increase headroom and watch the next capacity trend.",
                        "Validate request and limit settings against real usage.",
                    ],
                ),
                FinOpsForecastOut(
                    kind=FinOpsForecastKind.traffic,
                    scope_kind=self._normalize_scope_kind("service"),
                    scope_name="checkout-api",
                    headline="checkout-api traffic growth may drive avoidable spend",
                    summary="The sample scenario keeps one eye on a latency-heavy service that could become more expensive if growth continues unchecked.",
                    horizon_days=21,
                    confidence=0.8,
                    risk_level="elevated",
                    evidence=["Sample performance trend"],
                    recommendations=[
                        "Tune caching and retry behavior.",
                        "Watch request growth against the current autoscaling profile.",
                    ],
                ),
                FinOpsForecastOut(
                    kind=FinOpsForecastKind.reliability,
                    scope_kind=self._normalize_scope_kind("workload"),
                    scope_name="checkout-deployment",
                    headline="checkout-deployment reliability risk is still active",
                    summary="The sample scenario keeps a small reliability reserve on the busiest workload so operators can stay ahead of the next incident.",
                    horizon_days=14,
                    confidence=0.84,
                    risk_level="high",
                    evidence=["Sample incident", "Sample health score at 68/100"],
                    recommendations=[
                        "Treat the incident risk as a reliability investment decision.",
                        "Review the dependency chain before the next release.",
                    ],
                ),
            ],
            recommendations=[
                "Right-size the main production cluster before the next growth wave.",
                "Use the cheapest evidence-backed fix first: requests, limits, caching, or retention.",
                "Keep a little buffer in the busiest workload so the next spike stays visible.",
            ],
            top_scope="payments-prod",
        )
