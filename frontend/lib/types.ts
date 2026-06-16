/** Shared data contracts for the workspace UI. */

export type BackendMode = "live" | "demo";

export type TelemetrySourceType = "sample" | "otlp" | "cloudwatch" | "openobserve";
export type TelemetrySignalKind = "log" | "metric" | "trace" | "event" | "alert" | "security_event";
export type TelemetrySeverity = "debug" | "info" | "warning" | "error" | "critical";

export type AnalysisFindingCategory = "reliability" | "capacity" | "security" | "performance" | "anomaly";
export type AnalysisScopeKind = "service" | "workload" | "cluster" | "namespace";
export type AnalysisIncidentState = "open" | "acknowledged" | "investigating" | "resolved";
export type AnalysisHealthStatus = "healthy" | "watch" | "degraded" | "critical";
export type AlertKind = "incident" | "health";

export interface BackendHealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
  telemetry: string;
}

export interface ReadyDatabaseStatus {
  status: "ready" | "degraded";
  checked_at?: string | null;
  error?: string | null;
}

export interface TelemetryAdapterCapability {
  source_type: TelemetrySourceType;
  display_name: string;
  status: "ready" | "planned";
  deployment_model: "free-local" | "future-external";
  description: string;
}

export interface BackendReadyResponse {
  status: "ready" | "degraded";
  service: string;
  database: ReadyDatabaseStatus;
  adapters: TelemetryAdapterCapability[];
}

export interface AnalysisEvidenceItem {
  finding_id: string;
  telemetry_signal_id: string;
  title: string;
  summary: string;
  category: AnalysisFindingCategory;
  severity: TelemetrySeverity;
  confidence: number;
}

export interface AnalysisFinding {
  id: string;
  tenant_id: string;
  incident_id: string;
  telemetry_signal_id: string;
  correlation_key: string;
  source_name: string;
  source_type: TelemetrySourceType;
  observed_at: string;
  batch_label: string | null;
  category: AnalysisFindingCategory;
  kind: TelemetrySignalKind;
  severity: TelemetrySeverity;
  title: string;
  summary: string;
  confidence: number;
  evidence: Record<string, unknown>;
  recommendations: string[];
  service_name: string | null;
  workload_name: string | null;
  cluster_name: string | null;
  namespace: string | null;
  created_at: string;
}

export interface AnalysisIncident {
  id: string;
  tenant_id: string;
  correlation_key: string;
  scope_kind: AnalysisScopeKind;
  scope_name: string;
  state: AnalysisIncidentState;
  title: string;
  summary: string;
  probable_cause: string;
  confidence: number;
  evidence_count: number;
  finding_count: number;
  recommendations: string[];
  service_name: string | null;
  workload_name: string | null;
  cluster_name: string | null;
  namespace: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  evidence: AnalysisEvidenceItem[];
}

export interface AnalysisHealthScore {
  scope_kind: AnalysisScopeKind;
  scope_name: string;
  score: number;
  status: AnalysisHealthStatus;
  finding_count: number;
  incident_count: number;
  last_seen_at: string | null;
  primary_reason: string;
}

export interface GraphNode {
  id: string;
  label: string;
  kind: AnalysisScopeKind | "platform";
  status: AnalysisHealthStatus | "stable";
  score: number;
  incident_count: number;
  finding_count: number;
  description: string;
  x: number;
  y: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  weight: number;
}

export interface IncidentTimelineEntry {
  label: string;
  detail: string;
  at: string;
  tone: "neutral" | "warning" | "critical" | "success";
}

export interface PostmortemSection {
  title: string;
  body: string;
}

export interface PostmortemSummary {
  headline: string;
  summary: string;
  sections: PostmortemSection[];
  action_items: string[];
}

export interface DashboardStats {
  openIncidents: number;
  criticalFindings: number;
  watchServices: number;
  averageHealth: number;
  topService: string;
  latestSignal: string;
}

export interface AlertsSummary {
  total: number;
  incidents: number;
  health: number;
  security: number;
  critical: number;
  warning: number;
  info: number;
  scopes: number;
}

export interface WorkspaceAlert {
  id: string;
  tenantId: string;
  kind: AlertKind;
  severity: TelemetrySeverity;
  scopeKind: AnalysisScopeKind;
  scopeName: string;
  title: string;
  summary: string;
  sourceLabel: string;
  sourceDetail: string;
  actionLabel: string;
  href: string;
  confidence: number;
  evidenceCount: number;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  slackPreview: string;
}

export interface AlertsFeed {
  mode: BackendMode;
  generatedAt: string;
  sourceLabel: string;
  sourceReason: string;
  summary: AlertsSummary;
  copilotPrompt: string;
  slackPreview: string;
  alerts: WorkspaceAlert[];
}

export interface CopilotEvaluation {
  policy: string;
  faithfulness: number;
  answerRelevancy: number;
  contextPrecision: number;
  summary: string;
}

export interface CopilotAnswer {
  mode: BackendMode;
  generatedAt: string;
  sourceLabel: string;
  sourceReason: string;
  question: string;
  provider: string;
  usedFallback: boolean;
  answer: string;
  confidence: number;
  followUp: string;
  evidence: string[];
  evaluation: CopilotEvaluation;
  topAlertTitle: string | null;
  topAlertScope: string | null;
  topAlertSeverity: string | null;
}

export interface InvestigationBundle {
  mode: BackendMode;
  generatedAt: string;
  sourceLabel: string;
  sourceReason: string;
  backendHealth: BackendHealthResponse | null;
  backendReady: BackendReadyResponse | null;
  findings: AnalysisFinding[];
  incidents: AnalysisIncident[];
  healthScores: AnalysisHealthScore[];
  graph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  postmortem: PostmortemSummary;
  stats: DashboardStats;
}
