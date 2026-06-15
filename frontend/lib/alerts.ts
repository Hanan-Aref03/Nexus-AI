/** Alert feed derivation helpers for the workspace inbox. */

import type {
  AlertsFeed,
  AlertsSummary,
  AnalysisHealthScore,
  AnalysisIncident,
  BackendMode,
  InvestigationBundle,
  TelemetrySeverity,
  WorkspaceAlert,
} from "@/lib/types";

function severityOrder(severity: TelemetrySeverity): number {
  switch (severity) {
    case "critical":
      return 4;
    case "error":
      return 3;
    case "warning":
      return 2;
    case "info":
      return 1;
    default:
      return 0;
  }
}

function sortAlerts(alerts: WorkspaceAlert[]): WorkspaceAlert[] {
  return alerts.slice().sort((left, right) => {
    const severityDelta = severityOrder(right.severity) - severityOrder(left.severity);
    if (severityDelta !== 0) {
      return severityDelta;
    }

    return new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime();
  });
}

function hasSecurityEvidence(incident: AnalysisIncident): boolean {
  return (
    incident.probable_cause.toLowerCase().includes("security") ||
    incident.evidence.some((item) => item.category === "security") ||
    incident.recommendations.some((item) => item.toLowerCase().includes("security"))
  );
}

function buildIncidentAlert(incident: AnalysisIncident): WorkspaceAlert | null {
  if (incident.state === "resolved") {
    return null;
  }

  const security = hasSecurityEvidence(incident);
  const severity: TelemetrySeverity = security || incident.confidence >= 0.9 || incident.evidence_count >= 3 ? "critical" : "warning";
  const scopeLabel = `${incident.scope_kind.replace(/_/g, " ")} ${incident.scope_name}`;

  return {
    id: `incident-${incident.id}`,
    tenantId: incident.tenant_id,
    kind: "incident",
    severity,
    scopeKind: incident.scope_kind,
    scopeName: incident.scope_name,
    title: incident.title,
    summary: incident.summary,
    sourceLabel: scopeLabel.replace(/\b\w/g, (character) => character.toUpperCase()),
    sourceDetail: `${incident.evidence_count} evidence item(s) across ${incident.finding_count} finding(s)`,
    actionLabel: "Open incident",
    href: `/incidents/${incident.id}`,
    confidence: incident.confidence,
    evidenceCount: incident.evidence_count,
    tags: [incident.state, incident.scope_kind, ...(security ? ["security"] : [])],
    createdAt: incident.created_at,
    updatedAt: incident.updated_at,
    slackPreview: `${incident.title} | ${incident.probable_cause}`,
  };
}

function buildHealthAlert(score: AnalysisHealthScore): WorkspaceAlert | null {
  if (score.status === "healthy") {
    return null;
  }

  const severity: TelemetrySeverity = score.status === "critical" ? "critical" : score.status === "degraded" ? "warning" : "info";
  const scopeLabel = `${score.scope_kind.replace(/_/g, " ")} ${score.scope_name}`;
  const observedAt = score.last_seen_at ?? new Date().toISOString();

  return {
    id: `health-${score.scope_kind}-${score.scope_name}`,
    tenantId: "workspace",
    kind: "health",
    severity,
    scopeKind: score.scope_kind,
    scopeName: score.scope_name,
    title: `${score.scope_name} health score is ${score.score}`,
    summary: score.primary_reason,
    sourceLabel: scopeLabel.replace(/\b\w/g, (character) => character.toUpperCase()),
    sourceDetail: `${score.finding_count} finding(s) across ${score.incident_count} incident(s)`,
    actionLabel: "Open impact map",
    href: "/graph",
    confidence: score.score / 100,
    evidenceCount: score.finding_count,
    tags: [score.scope_kind, score.status],
    createdAt: observedAt,
    updatedAt: observedAt,
    slackPreview: `${score.scope_name} is ${score.status} at ${score.score}/100. ${score.primary_reason}`,
  };
}

function buildCopilotPrompt(alert: WorkspaceAlert): string {
  if (alert.kind === "incident" && alert.tags.includes("security")) {
    return `What evidence supports the security incident in ${alert.scopeName}, and what should we do first?`;
  }

  if (alert.kind === "incident") {
    return `What evidence explains the incident in ${alert.scopeName}, and what is the safest next step?`;
  }

  return `Why is ${alert.scopeName} degraded, and which follow-up should we review first?`;
}

function buildSlackPreview(alert: WorkspaceAlert): string {
  return `[${alert.severity.toUpperCase()}] ${alert.title} - ${alert.summary} | ${alert.actionLabel}`;
}

function summarizeAlerts(alerts: WorkspaceAlert[]): AlertsSummary {
  const uniqueScopes = new Set(alerts.map((alert) => `${alert.scopeKind}:${alert.scopeName}`));

  return {
    total: alerts.length,
    incidents: alerts.filter((alert) => alert.kind === "incident").length,
    health: alerts.filter((alert) => alert.kind === "health").length,
    security: alerts.filter((alert) => alert.tags.includes("security")).length,
    critical: alerts.filter((alert) => alert.severity === "critical").length,
    warning: alerts.filter((alert) => alert.severity === "warning").length,
    info: alerts.filter((alert) => alert.severity === "info").length,
    scopes: uniqueScopes.size,
  };
}

export function buildAlertsFeedFromBundle(bundle: InvestigationBundle): AlertsFeed {
  const alerts = sortAlerts([
    ...bundle.incidents.map(buildIncidentAlert).filter((alert): alert is WorkspaceAlert => alert !== null),
    ...bundle.healthScores.map(buildHealthAlert).filter((alert): alert is WorkspaceAlert => alert !== null),
  ]);
  const summary = summarizeAlerts(alerts);
  const topAlert = alerts[0];

  return {
    mode: bundle.mode,
    generatedAt: new Date().toISOString(),
    sourceLabel: bundle.sourceLabel,
    sourceReason: `${bundle.sourceReason} The same analysis state powers the alert inbox.`,
    summary,
    copilotPrompt: topAlert ? buildCopilotPrompt(topAlert) : "The workspace is calm right now. Which service should we inspect next?",
    slackPreview: topAlert ? buildSlackPreview(topAlert) : "No active alerts are ready for delivery.",
    alerts,
  };
}

export function buildCalmAlertsFeed(mode: BackendMode, sourceLabel: string, sourceReason: string): AlertsFeed {
  return {
    mode,
    generatedAt: new Date().toISOString(),
    sourceLabel,
    sourceReason,
    summary: {
      total: 0,
      incidents: 0,
      health: 0,
      security: 0,
      critical: 0,
      warning: 0,
      info: 0,
      scopes: 0,
    },
    copilotPrompt: "The workspace is calm right now. Which service should we inspect next?",
    slackPreview: "No active alerts are ready for delivery.",
    alerts: [],
  };
}
