/** Derivation helpers that turn raw workspace data into dashboard-ready views. */

import type {
  AnalysisFinding,
  AnalysisHealthScore,
  AnalysisIncident,
  DashboardStats,
  GraphEdge,
  GraphNode,
  IncidentTimelineEntry,
  PostmortemSummary,
} from "@/lib/types";

function uniqueList(values: string[]): string[] {
  return values.filter((value, index) => values.indexOf(value) === index);
}

function mostSevereFinding(findings: AnalysisFinding[]): AnalysisFinding | undefined {
  return findings.slice().sort((left, right) => {
    const severityOrder = { critical: 4, error: 3, warning: 2, info: 1, debug: 0 };
    return (
      severityOrder[right.severity as keyof typeof severityOrder] -
        severityOrder[left.severity as keyof typeof severityOrder] ||
      right.confidence - left.confidence
    );
  })[0];
}

export function buildDashboardStats(
  findings: AnalysisFinding[],
  incidents: AnalysisIncident[],
  healthScores: AnalysisHealthScore[],
): DashboardStats {
  const openIncidents = incidents.filter((incident) => incident.state !== "resolved").length;
  const criticalFindings = findings.filter((finding) => finding.severity === "critical").length;
  const watchServices = healthScores.filter((score) => score.status !== "healthy").length;
  const averageHealth = healthScores.length
    ? healthScores.reduce((sum, score) => sum + score.score, 0) / healthScores.length
    : 0;
  const topService = healthScores.slice().sort((left, right) => left.score - right.score)[0]?.scope_name ?? "n/a";
  const latestSignal = findings.slice().sort((left, right) => {
    return new Date(right.observed_at).getTime() - new Date(left.observed_at).getTime();
  })[0]?.title ?? "No signals yet";

  return {
    openIncidents,
    criticalFindings,
    watchServices,
    averageHealth,
    topService,
    latestSignal,
  };
}

export function buildIncidentTimeline(incident: AnalysisIncident): IncidentTimelineEntry[] {
  const timeline: IncidentTimelineEntry[] = [
    {
      label: "Incident opened",
      detail: incident.title,
      at: incident.created_at,
      tone: "critical",
    },
    {
      label: "Last updated",
      detail: incident.summary,
      at: incident.updated_at,
      tone: "warning",
    },
  ];

  if (incident.resolved_at) {
    timeline.push({
      label: "Resolved",
      detail: "Incident was marked resolved by an operator.",
      at: incident.resolved_at,
      tone: "success",
    });
  }

  for (const evidence of incident.evidence.slice(0, 4)) {
    timeline.push({
      label: "Evidence observed",
      detail: evidence.summary,
      at: evidence.confidence > 0.9 ? incident.created_at : incident.updated_at,
      tone: evidence.severity === "critical" || evidence.severity === "error" ? "critical" : "neutral",
    });
  }

  return timeline.sort((left, right) => new Date(left.at).getTime() - new Date(right.at).getTime());
}

export function buildPostmortemSummary(
  incidents: AnalysisIncident[],
  findings: AnalysisFinding[],
): PostmortemSummary {
  const focusIncident = incidents[0];
  const focusFinding = mostSevereFinding(findings);

  if (!focusIncident) {
    return {
      headline: "No incident generated yet",
      summary: "The workspace will populate automatically once detection starts producing incidents.",
      sections: [
        {
          title: "What to watch",
          body: "Open incidents, evidence, and timeline entries will appear here as soon as the workspace starts receiving signals.",
        },
      ],
      action_items: ["Start detection", "Review the first correlated incident"],
    };
  }

  const impact = uniqueList(
    incidents
      .map((incident) => incident.service_name ?? incident.workload_name ?? incident.scope_name)
      .filter((value): value is string => Boolean(value)),
  );

  return {
    headline: focusIncident.title,
    summary: `Likely cause: ${focusIncident.probable_cause}. Confidence is ${Math.round(focusIncident.confidence * 100)}%. Top evidence: ${
      focusFinding?.title ?? "the strongest correlated finding"
    }.`,
    sections: [
      {
        title: "What happened",
        body: focusIncident.summary,
      },
      {
        title: "Why it mattered",
        body: `The affected scope is ${focusIncident.scope_kind} "${focusIncident.scope_name}", with ${focusIncident.evidence_count} correlated signal(s).`,
      },
      {
        title: "Recommended response",
        body: uniqueList(focusIncident.recommendations).slice(0, 3).join(". "),
      },
    ],
    action_items: uniqueList([
      "Acknowledge the incident in the operations console",
      ...focusIncident.recommendations.slice(0, 2),
      `Share the postmortem with owners of ${impact.join(", ") || focusIncident.scope_name}`,
    ]),
  };
}

export function buildDependencyGraph(
  incidents: AnalysisIncident[],
  healthScores: AnalysisHealthScore[],
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const platformNode: GraphNode = {
    id: "nexusai-core",
    label: "NexusAI Core",
    kind: "platform",
    status: "stable",
    score: 100,
    incident_count: incidents.length,
    finding_count: incidents.reduce((sum, incident) => sum + incident.finding_count, 0),
    description: "The central observability and investigation plane that stitches services together.",
    x: 50,
    y: 50,
  };

  const sortedScores = healthScores.slice().sort((left, right) => left.score - right.score);
  const radius = 34;
  const total = Math.max(sortedScores.length, 1);

  const nodes: GraphNode[] = [platformNode];
  const edges: GraphEdge[] = [];

  sortedScores.forEach((score, index) => {
    const angle = (Math.PI * 2 * index) / total - Math.PI / 2;
    const x = Math.round(50 + radius * Math.cos(angle));
    const y = Math.round(50 + radius * Math.sin(angle));
    const matchingIncidents = incidents.filter(
      (incident) => incident.scope_name === score.scope_name || incident.service_name === score.scope_name,
    );

    nodes.push({
      id: `service-${score.scope_name}`,
      label: score.scope_name,
      kind: score.scope_kind,
      status: score.status,
      score: score.score,
      incident_count: matchingIncidents.length,
      finding_count: matchingIncidents.reduce((sum, incident) => sum + incident.finding_count, 0),
      description: score.primary_reason,
      x,
      y,
    });

    edges.push({
      id: `edge-${platformNode.id}-${score.scope_name}`,
      source: platformNode.id,
      target: `service-${score.scope_name}`,
      label: score.status === "critical" ? "blast radius" : score.status === "degraded" ? "shared dependency" : "healthy path",
      weight: score.status === "critical" ? 4 : score.status === "degraded" ? 3 : 1,
    });
  });

  return { nodes, edges };
}
