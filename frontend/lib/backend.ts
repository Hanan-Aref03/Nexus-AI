/** Server-side backend access helpers for the live dashboard experience. */

import { buildDemoInvestigationBundle } from "@/lib/demo-data";
import { buildAlertsFeedFromBundle } from "@/lib/alerts";
import { buildFinOpsInsightsFromBundle, normalizeBackendFinOpsInsights } from "@/lib/finops";
import { createBackendAccessToken } from "@/lib/auth-server";
import type { AuthSession } from "@/lib/auth";
import { buildDashboardStats, buildDependencyGraph, buildPostmortemSummary } from "@/lib/insights";
import type {
  AlertKind,
  AlertsFeed,
  AlertsSummary,
  AnalysisScopeKind,
  AnalysisFinding,
  AnalysisHealthScore,
  AnalysisIncident,
  BackendHealthResponse,
  BackendReadyResponse,
  FinOpsInsights,
  InvestigationBundle,
  TelemetrySeverity,
  WorkspaceAlert,
} from "@/lib/types";

function getBackendBaseUrl(): string {
  return process.env.BACKEND_BASE_URL ?? process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
}

interface BackendAlertSummary extends AlertsSummary {}

interface BackendWorkspaceAlert {
  id: string;
  tenant_id: string;
  kind: AlertKind;
  severity: TelemetrySeverity;
  scope_kind: AnalysisScopeKind;
  scope_name: string;
  title: string;
  summary: string;
  source_label: string;
  source_detail: string;
  action_label: string;
  href: string;
  confidence: number;
  evidence_count: number;
  tags: string[];
  created_at: string;
  updated_at: string;
  slack_preview: string;
}

interface BackendAlertsFeedResponse {
  mode: "live" | "demo";
  generated_at: string;
  source_label: string;
  source_reason: string;
  summary: BackendAlertSummary;
  copilot_prompt: string;
  slack_preview: string;
  alerts: BackendWorkspaceAlert[];
}

interface BackendFinOpsInsightsResponse {
  mode: "live" | "demo";
  generated_at: string;
  source_label: string;
  source_reason: string;
  estimated_monthly_savings: number;
  risk_score: number;
  opportunity_count: number;
  forecast_count: number;
  opportunities: Array<{
    kind: "rightsizing" | "idle_resource" | "efficiency" | "reliability";
    scope_kind: "service" | "workload" | "cluster" | "namespace";
    scope_name: string;
    headline: string;
    summary: string;
    estimated_monthly_savings: number;
    confidence: number;
    risk_level: string;
    evidence: string[];
    recommendations: string[];
    horizon_days: number;
  }>;
  forecasts: Array<{
    kind: "storage" | "saturation" | "traffic" | "reliability";
    scope_kind: "service" | "workload" | "cluster" | "namespace" | null;
    scope_name: string | null;
    headline: string;
    summary: string;
    horizon_days: number;
    confidence: number;
    risk_level: string;
    evidence: string[];
    recommendations: string[];
  }>;
  recommendations: string[];
  top_scope: string | null;
}

async function fetchJson<T>(path: string, session: AuthSession | null): Promise<T> {
  const response = await fetch(`${getBackendBaseUrl()}${path}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${createBackendAccessToken(session)}`,
      "X-Tenant-Id": session?.tenantId ?? process.env.NEXUSAI_TENANT_ID ?? "platform-demo",
      "X-User-Role": session?.role ?? "viewer",
      "X-User-Email": session?.email ?? "demo@nexusai.local",
    },
  });

  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}.`);
  }

  return (await response.json()) as T;
}

async function fetchOptionalJson<T>(path: string, session: AuthSession | null): Promise<T | null> {
  try {
    return await fetchJson<T>(path, session);
  } catch {
    return null;
  }
}

function normalizeBackendAlertsFeed(feed: BackendAlertsFeedResponse): AlertsFeed {
  return {
    mode: feed.mode,
    generatedAt: feed.generated_at,
    sourceLabel: feed.source_label,
    sourceReason: feed.source_reason,
    summary: feed.summary,
    copilotPrompt: feed.copilot_prompt,
    slackPreview: feed.slack_preview,
    alerts: feed.alerts.map(
      (alert): WorkspaceAlert => ({
        id: alert.id,
        tenantId: alert.tenant_id,
        kind: alert.kind,
        severity: alert.severity,
        scopeKind: alert.scope_kind,
        scopeName: alert.scope_name,
        title: alert.title,
        summary: alert.summary,
        sourceLabel: alert.source_label,
        sourceDetail: alert.source_detail,
        actionLabel: alert.action_label,
        href: alert.href,
        confidence: alert.confidence,
        evidenceCount: alert.evidence_count,
        tags: alert.tags,
        createdAt: alert.created_at,
        updatedAt: alert.updated_at,
        slackPreview: alert.slack_preview,
      }),
    ),
  };
}

function buildLiveBundle(
  health: BackendHealthResponse | null,
  ready: BackendReadyResponse | null,
  findings: AnalysisFinding[],
  incidents: AnalysisIncident[],
  healthScores: AnalysisHealthScore[],
): InvestigationBundle {
  const hasVisibleData = findings.length > 0 || incidents.length > 0 || healthScores.length > 0;

  if (!hasVisibleData) {
    const demo = buildDemoInvestigationBundle("demo");
    return {
      ...demo,
      backendHealth: health,
      backendReady: ready,
      sourceLabel: "Sample workspace data",
      sourceReason: "No live workspace data is available yet, so a curated scenario is shown instead.",
      generatedAt: new Date().toISOString(),
    };
  }

  return {
    mode: "live",
    generatedAt: new Date().toISOString(),
    sourceLabel: "Live workspace data",
    sourceReason: "The workspace is reading the current investigation data for this tenant.",
    backendHealth: health,
    backendReady: ready,
    findings,
    incidents,
    healthScores,
    graph: buildDependencyGraph(incidents, healthScores),
    postmortem: buildPostmortemSummary(incidents, findings),
    stats: buildDashboardStats(findings, incidents, healthScores),
  };
}

export async function loadInvestigationBundle(session: AuthSession | null = null): Promise<InvestigationBundle> {
  const [health, ready, findings, incidents, healthScores] = await Promise.all([
    fetchOptionalJson<BackendHealthResponse>("/health", session),
    fetchOptionalJson<BackendReadyResponse>("/ready", session),
    fetchOptionalJson<AnalysisFinding[]>("/api/v1/analysis/findings?limit=100", session),
    fetchOptionalJson<AnalysisIncident[]>("/api/v1/analysis/incidents?limit=50", session),
    fetchOptionalJson<AnalysisHealthScore[]>("/api/v1/analysis/health-scores?limit=50", session),
  ]);

  if (!health && !ready && !findings && !incidents && !healthScores) {
    return buildDemoInvestigationBundle("demo");
  }

  return buildLiveBundle(health, ready, findings ?? [], incidents ?? [], healthScores ?? []);
}

export async function loadIncidentBundle(
  incidentId: string,
  session: AuthSession | null = null,
): Promise<{
  bundle: InvestigationBundle;
  incident: AnalysisIncident | null;
}> {
  const bundle = await loadInvestigationBundle(session);
  const liveIncident = await fetchOptionalJson<AnalysisIncident>(`/api/v1/analysis/incidents/${incidentId}`, session);
  const incident = liveIncident ?? bundle.incidents.find((item) => item.id === incidentId) ?? null;

  return {
    bundle,
    incident,
  };
}

export async function loadAlertsFeed(session: AuthSession | null = null): Promise<AlertsFeed> {
  const liveFeed = await fetchOptionalJson<BackendAlertsFeedResponse>("/api/v1/alerts?limit=12", session);
  if (liveFeed) {
    return normalizeBackendAlertsFeed(liveFeed);
  }

  const bundle = await loadInvestigationBundle(session);
  return buildAlertsFeedFromBundle(bundle);
}

export async function loadFinOpsInsights(session: AuthSession | null = null): Promise<FinOpsInsights> {
  const liveInsights = await fetchOptionalJson<BackendFinOpsInsightsResponse>("/api/v1/finops/insights?limit=100", session);
  if (liveInsights) {
    return normalizeBackendFinOpsInsights(liveInsights);
  }

  const bundle = await loadInvestigationBundle(session);
  return buildFinOpsInsightsFromBundle(bundle);
}
