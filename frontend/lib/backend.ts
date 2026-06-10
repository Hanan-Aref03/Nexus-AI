/** Server-side backend access helpers for the live dashboard experience. */

import { buildDemoInvestigationBundle } from "@/lib/demo-data";
import { createBackendAccessToken } from "@/lib/auth-server";
import type { AuthSession } from "@/lib/auth";
import { buildDashboardStats, buildDependencyGraph, buildPostmortemSummary } from "@/lib/insights";
import type {
  AnalysisFinding,
  AnalysisHealthScore,
  AnalysisIncident,
  BackendHealthResponse,
  BackendReadyResponse,
  InvestigationBundle,
} from "@/lib/types";

function getBackendBaseUrl(): string {
  return process.env.BACKEND_BASE_URL ?? process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
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
