/** FinOps derivation helpers for the final predictive-reliability slice. */

import type {
  AnalysisFinding,
  AnalysisHealthScore,
  AnalysisIncident,
  AnalysisScopeKind,
  BackendMode,
  FinOpsForecast,
  FinOpsForecastKind,
  FinOpsInsights,
  FinOpsOpportunity,
  FinOpsOpportunityKind,
  InvestigationBundle,
} from "@/lib/types";

interface BackendFinOpsOpportunity {
  kind: FinOpsOpportunityKind;
  scope_kind: AnalysisScopeKind;
  scope_name: string;
  headline: string;
  summary: string;
  estimated_monthly_savings: number;
  confidence: number;
  risk_level: string;
  evidence: string[];
  recommendations: string[];
  horizon_days: number;
}

interface BackendFinOpsForecast {
  kind: FinOpsForecastKind;
  scope_kind: AnalysisScopeKind | null;
  scope_name: string | null;
  headline: string;
  summary: string;
  horizon_days: number;
  confidence: number;
  risk_level: string;
  evidence: string[];
  recommendations: string[];
}

interface BackendFinOpsInsightsResponse {
  mode: BackendMode;
  generated_at: string;
  source_label: string;
  source_reason: string;
  estimated_monthly_savings: number;
  risk_score: number;
  opportunity_count: number;
  forecast_count: number;
  opportunities: BackendFinOpsOpportunity[];
  forecasts: BackendFinOpsForecast[];
  recommendations: string[];
  top_scope: string | null;
}

interface ScopeLike {
  service_name?: string | null;
  workload_name?: string | null;
  cluster_name?: string | null;
  namespace?: string | null;
  scope_name?: string | null;
}

function uniqueList(values: string[]): string[] {
  return values.filter((value, index) => value && values.indexOf(value) === index);
}

function normalizedScopeKey(item: ScopeLike): string {
  return (
    item.service_name ??
    item.workload_name ??
    item.cluster_name ??
    item.namespace ??
    item.scope_name ??
    "workspace"
  );
}

function normalizedScopeKind(item: ScopeLike): AnalysisScopeKind {
  if (item.service_name) {
    return "service";
  }
  if (item.workload_name) {
    return "workload";
  }
  if (item.cluster_name) {
    return "cluster";
  }
  return "namespace";
}

function estimateSavings(score: AnalysisHealthScore | undefined, findings: AnalysisFinding[], incidents: AnalysisIncident[]): number {
  const capacityCount = findings.filter((finding) => finding.category === "capacity").length;
  const performanceCount = findings.filter((finding) => finding.category === "performance").length;
  const reliabilityCount = findings.filter((finding) => finding.category === "reliability").length;
  const openIncidents = incidents.filter((incident) => incident.state !== "resolved").length;
  const healthPenalty = score && score.status !== "healthy" ? (100 - score.score) * 1.5 : 0;

  const raw =
    capacityCount * 120 +
    Math.max(0, capacityCount - 1) * 30 +
    performanceCount * 60 +
    reliabilityCount * 45 +
    openIncidents * 35 +
    healthPenalty;

  return Number(Math.min(950, Math.max(0, raw)).toFixed(2));
}

function scoreConfidence(score: AnalysisHealthScore | undefined, findings: AnalysisFinding[]): number {
  const base = 0.55 + Math.min(findings.length, 4) * 0.06 + (score && score.status !== "healthy" ? 0.06 : 0);
  return Number(Math.min(0.96, base).toFixed(2));
}

function scoreRiskLevel(score: AnalysisHealthScore | undefined, findings: AnalysisFinding[], incidents: AnalysisIncident[]): string {
  const openIncidents = incidents.filter((incident) => incident.state !== "resolved").length;
  if ((score && score.score < 65) || openIncidents >= 2 || findings.length >= 4) {
    return "high";
  }
  if ((score && score.score < 82) || openIncidents === 1 || findings.length >= 2) {
    return "elevated";
  }
  return "watch";
}

function scoreHorizon(score: AnalysisHealthScore | undefined, findings: AnalysisFinding[], incidents: AnalysisIncident[]): number {
  const openIncidents = incidents.filter((incident) => incident.state !== "resolved").length;
  const raw = 42 - findings.length * 4 - openIncidents * 3 - (score ? Math.max(0, 90 - score.score) / 5 : 0);
  return Math.max(7, Math.min(42, Math.round(raw)));
}

function buildOpportunity(
  scopeKind: AnalysisScopeKind,
  scopeName: string,
  findings: AnalysisFinding[],
  incidents: AnalysisIncident[],
  score: AnalysisHealthScore | undefined,
): FinOpsOpportunity | null {
  if (!findings.length && !score) {
    return null;
  }

  const capacityFindings = findings.filter((finding) => finding.category === "capacity");
  const performanceFindings = findings.filter((finding) => finding.category === "performance");
  const reliabilityFindings = findings.filter((finding) => finding.category === "reliability");
  const savings = estimateSavings(score, findings, incidents);
  if (savings <= 0 && !capacityFindings.length && !performanceFindings.length && !reliabilityFindings.length) {
    return null;
  }

  const kind: FinOpsOpportunityKind =
    capacityFindings.length > 0
      ? score && score.score < 85
        ? "rightsizing"
        : "idle_resource"
      : performanceFindings.length > 0
        ? "efficiency"
        : "reliability";

  const headline =
    kind === "rightsizing"
      ? `${scopeName} can be right-sized`
      : kind === "idle_resource"
        ? `${scopeName} has spare headroom`
        : kind === "efficiency"
          ? `${scopeName} is spending headroom on latency`
          : `${scopeName} needs a reliability budget check`;

  const summary = [
    `${scopeName} has ${findings.length} correlated finding(s).`,
    capacityFindings.length
      ? `${capacityFindings.length} capacity signal(s) suggest unused headroom or oversized requests.`
      : "",
    performanceFindings.length
      ? `${performanceFindings.length} performance signal(s) point at extra spend on latency or scaling pressure.`
      : "",
    score ? `Health is ${score.score}/100, which keeps the opportunity evidence-backed.` : "",
    incidents.some((incident) => incident.state !== "resolved")
      ? "An unresolved incident is still amplifying the waste signal."
      : "",
  ]
    .filter(Boolean)
    .join(" ");

  const evidence = uniqueList([
    ...findings.slice(0, 2).map((finding) => finding.title),
    score?.primary_reason ?? "",
    ...incidents.slice(0, 1).map((incident) => incident.title),
  ]);

  return {
    kind,
    scopeKind,
    scopeName,
    headline,
    summary,
    estimatedMonthlySavings: savings,
    confidence: scoreConfidence(score, findings),
    riskLevel: scoreRiskLevel(score, findings, incidents),
    evidence: evidence.slice(0, 4),
    recommendations: uniqueList([
      ...(capacityFindings.length
        ? [
            `Right-size the requests or limits for ${scopeName}.`,
            "Validate that the observed headroom is not hiding a bursty workload.",
          ]
        : []),
      ...(performanceFindings.length
        ? [
            `Reduce the hot-path latency for ${scopeName} before autoscaling waste grows.`,
            "Check traces, caching, and downstream dependencies.",
          ]
        : []),
      ...(reliabilityFindings.length
        ? [
            "Treat the remaining reliability risk as a budget issue, not just an SRE issue.",
            "Keep one eye on error budgets while you tune the resource footprint.",
          ]
        : []),
    ]).slice(0, 3),
    horizonDays: scoreHorizon(score, findings, incidents),
  };
}

function buildForecast(
  kind: FinOpsForecastKind,
  scopeKind: AnalysisScopeKind,
  scopeName: string,
  findings: AnalysisFinding[],
  incidents: AnalysisIncident[],
  score: AnalysisHealthScore | undefined,
): FinOpsForecast {
  const openIncidents = incidents.filter((incident) => incident.state !== "resolved").length;
  const pressure = Math.max(1, findings.length);
  const horizonBase =
    kind === "storage"
      ? 30
      : kind === "saturation"
        ? 28
        : kind === "traffic"
          ? 35
          : 24;
  const horizonDays = Math.max(7, Math.min(60, Math.round(horizonBase - pressure * 3 - openIncidents * 2 - (score ? Math.max(0, 85 - score.score) / 5 : 0))));
  const riskLevel = horizonDays <= 14 ? "high" : horizonDays <= 28 ? "elevated" : "watch";
  const confidence = Number(Math.min(0.95, 0.58 + Math.min(findings.length, 3) * 0.05 + (score && score.status !== "healthy" ? 0.05 : 0)).toFixed(2));

  const headline =
    kind === "storage"
      ? `${scopeName} storage could become the next bottleneck`
      : kind === "saturation"
        ? `${scopeName} is trending toward saturation`
        : kind === "traffic"
          ? `${scopeName} traffic growth may drive avoidable spend`
          : `${scopeName} reliability risk is still active`;

  const summary =
    kind === "storage"
      ? `Capacity signals on ${scopeName} point to storage or memory pressure if the trend keeps climbing.`
      : kind === "saturation"
        ? `Current pressure on ${scopeName} suggests that resource headroom is shrinking.`
        : kind === "traffic"
          ? `Performance signals on ${scopeName} imply the autoscaling or caching strategy should be revisited.`
          : `Open incidents on ${scopeName} are still consuming budget that should go to stability work.`;

  const recommendations =
    kind === "storage"
      ? [
          "Trim retention or scale the storage-heavy path before the line bends upward again.",
          "Set a tighter watch on disk or memory growth so the next threshold is visible earlier.",
        ]
      : kind === "saturation"
        ? [
            "Validate request and limit settings against actual usage.",
            "Reserve a little headroom before the next traffic spike arrives.",
          ]
        : kind === "traffic"
          ? [
              "Check the hot path for caching, batching, or retry amplification opportunities.",
              "Compare current request growth against the expected baseline and tune alerts accordingly.",
            ]
          : [
              "Treat the remaining incident risk as a reliability investment decision.",
              "Review the dependency chain and the error budget before the next release.",
            ];

  const evidence = uniqueList([
    ...findings.slice(0, 2).map((finding) => finding.title),
    score?.primary_reason ?? "",
    ...incidents.slice(0, 1).map((incident) => incident.title),
  ]);

  return {
    kind,
    scopeKind,
    scopeName,
    headline,
    summary,
    horizonDays,
    confidence,
    riskLevel,
    evidence: evidence.slice(0, 3),
    recommendations,
  };
}

function buildForecastsFromBundle(bundle: InvestigationBundle): FinOpsForecast[] {
  const findingsByScope = new Map<string, AnalysisFinding[]>();
  const incidentsByScope = new Map<string, AnalysisIncident[]>();
  const healthByScope = new Map<string, AnalysisHealthScore>();

  for (const finding of bundle.findings) {
    const scopeName = normalizedScopeKey(finding);
    const current = findingsByScope.get(scopeName) ?? [];
    current.push(finding);
    findingsByScope.set(scopeName, current);
  }

  for (const incident of bundle.incidents) {
    const scopeName = normalizedScopeKey(incident);
    const current = incidentsByScope.get(scopeName) ?? [];
    current.push(incident);
    incidentsByScope.set(scopeName, current);
  }

  for (const score of bundle.healthScores) {
    healthByScope.set(score.scope_name, score);
  }

  const forecasts: FinOpsForecast[] = [];
  for (const [scopeName, scopeFindings] of findingsByScope.entries()) {
    const health = healthByScope.get(scopeName);
    const scopeKind = health?.scope_kind ?? normalizedScopeKind(scopeFindings[0]);
    const scopeIncidents = incidentsByScope.get(scopeName) ?? [];
    const categories = new Set(scopeFindings.map((finding) => finding.category));

    if (categories.has("capacity") || (health && health.status !== "healthy")) {
      forecasts.push(buildForecast("saturation", scopeKind, scopeName, scopeFindings, scopeIncidents, health));
    }
    if (scopeFindings.some((finding) => finding.summary.toLowerCase().includes("disk") || finding.summary.toLowerCase().includes("storage"))) {
      forecasts.push(buildForecast("storage", scopeKind, scopeName, scopeFindings, scopeIncidents, health));
    }
    if (categories.has("performance")) {
      forecasts.push(buildForecast("traffic", scopeKind, scopeName, scopeFindings, scopeIncidents, health));
    }
    if (categories.has("reliability") || scopeIncidents.some((incident) => incident.state !== "resolved")) {
      forecasts.push(buildForecast("reliability", scopeKind, scopeName, scopeFindings, scopeIncidents, health));
    }
  }

  if (forecasts.length === 0) {
    const fallbackScope = bundle.healthScores[0]?.scope_name ?? (bundle.findings[0] ? normalizedScopeKey(bundle.findings[0]) : "workspace");
    const fallbackKind =
      bundle.healthScores[0]?.scope_kind ??
      normalizedScopeKind(bundle.findings[0] ?? { service_name: fallbackScope, workload_name: null, cluster_name: null, namespace: null });
    forecasts.push({
      kind: "reliability",
      scopeKind: fallbackKind,
      scopeName: fallbackScope,
      headline: `${fallbackScope} reliability should stay under watch`,
      summary: "The current workspace does not show an immediate FinOps forecast yet, but the final phase keeps a conservative reliability check in place.",
      horizonDays: 42,
      confidence: 0.66,
      riskLevel: "watch",
      evidence: bundle.findings.slice(0, 2).map((finding) => finding.title),
      recommendations: [
        "Keep a small reliability reserve in the busiest scope.",
        "Review the next few telemetry batches before assuming the trend is flat.",
      ],
    });
  }

  return forecasts.sort((left, right) => left.horizonDays - right.horizonDays).slice(0, 4);
}

function buildOpportunitiesFromBundle(bundle: InvestigationBundle): FinOpsOpportunity[] {
  const findingsByScope = new Map<string, AnalysisFinding[]>();
  const incidentsByScope = new Map<string, AnalysisIncident[]>();
  const healthByScope = new Map<string, AnalysisHealthScore>();

  for (const finding of bundle.findings) {
    const scopeName = normalizedScopeKey(finding);
    const current = findingsByScope.get(scopeName) ?? [];
    current.push(finding);
    findingsByScope.set(scopeName, current);
  }

  for (const incident of bundle.incidents) {
    const scopeName = normalizedScopeKey(incident);
    const current = incidentsByScope.get(scopeName) ?? [];
    current.push(incident);
    incidentsByScope.set(scopeName, current);
  }

  for (const score of bundle.healthScores) {
    healthByScope.set(score.scope_name, score);
  }

  const opportunities: FinOpsOpportunity[] = [];
  for (const [scopeName, scopeFindings] of findingsByScope.entries()) {
    const health = healthByScope.get(scopeName);
    const scopeKind = health?.scope_kind ?? normalizedScopeKind(scopeFindings[0]);
    const scopeIncidents = incidentsByScope.get(scopeName) ?? [];
    const opportunity = buildOpportunity(scopeKind, scopeName, scopeFindings, scopeIncidents, health);
    if (opportunity) {
      opportunities.push(opportunity);
    }
  }

  return opportunities
    .sort((left, right) => right.estimatedMonthlySavings - left.estimatedMonthlySavings || right.confidence - left.confidence)
    .slice(0, 5);
}

export function normalizeBackendFinOpsInsights(response: BackendFinOpsInsightsResponse): FinOpsInsights {
  return {
    mode: response.mode,
    generatedAt: response.generated_at,
    sourceLabel: response.source_label,
    sourceReason: response.source_reason,
    estimatedMonthlySavings: response.estimated_monthly_savings,
    riskScore: response.risk_score,
    opportunityCount: response.opportunity_count,
    forecastCount: response.forecast_count,
    opportunities: response.opportunities.map(
      (item): FinOpsOpportunity => ({
        kind: item.kind,
        scopeKind: item.scope_kind,
        scopeName: item.scope_name,
        headline: item.headline,
        summary: item.summary,
        estimatedMonthlySavings: item.estimated_monthly_savings,
        confidence: item.confidence,
        riskLevel: item.risk_level,
        evidence: item.evidence,
        recommendations: item.recommendations,
        horizonDays: item.horizon_days,
      }),
    ),
    forecasts: response.forecasts.map(
      (item): FinOpsForecast => ({
        kind: item.kind,
        scopeKind: item.scope_kind,
        scopeName: item.scope_name,
        headline: item.headline,
        summary: item.summary,
        horizonDays: item.horizon_days,
        confidence: item.confidence,
        riskLevel: item.risk_level,
        evidence: item.evidence,
        recommendations: item.recommendations,
      }),
    ),
    recommendations: response.recommendations,
    topScope: response.top_scope,
  };
}

export function buildFinOpsInsightsFromBundle(bundle: InvestigationBundle): FinOpsInsights {
  const opportunities = buildOpportunitiesFromBundle(bundle);
  const forecasts = buildForecastsFromBundle(bundle);
  const estimatedMonthlySavings = Number(opportunities.reduce((sum, item) => sum + item.estimatedMonthlySavings, 0).toFixed(2));
  const riskScore = Math.min(
    100,
    18 +
      bundle.healthScores.filter((score) => score.status === "critical").length * 16 +
      bundle.healthScores.filter((score) => score.status === "degraded").length * 10 +
      bundle.healthScores.filter((score) => score.status === "watch").length * 6 +
      bundle.incidents.filter((incident) => incident.state !== "resolved").length * 9 +
      bundle.findings.filter((finding) => finding.category === "capacity").length * 5 +
      bundle.findings.filter((finding) => finding.category === "performance").length * 3 +
      bundle.findings.filter((finding) => finding.category === "reliability").length * 4,
  );
  const recommendations = uniqueList([
    ...opportunities.flatMap((item) => item.recommendations.slice(0, 2)),
    ...forecasts.flatMap((item) => item.recommendations.slice(0, 2)),
  ]).slice(0, 6);

  return {
    mode: bundle.mode,
    generatedAt: bundle.generatedAt,
    sourceLabel: bundle.sourceLabel,
    sourceReason: `${bundle.sourceReason} The same analysis state powers the FinOps lens.`,
    estimatedMonthlySavings,
    riskScore,
    opportunityCount: opportunities.length,
    forecastCount: forecasts.length,
    opportunities,
    forecasts,
    recommendations,
    topScope: opportunities[0]?.scopeName ?? forecasts[0]?.scopeName ?? null,
  };
}
