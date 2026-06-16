/** Shared auth and tenant helpers for the workspace shell. */

export type WorkspaceRole = "owner" | "incident_commander" | "analyst" | "service_owner" | "viewer";

export type WorkspaceRoute = "/" | "/alerts" | "/findings" | "/incidents" | "/graph" | "/postmortems" | "/finops";

export interface AuthSession {
  sessionId: string;
  userId: string;
  displayName: string;
  email: string;
  tenantId: string;
  tenantName: string;
  role: WorkspaceRole;
  permissions: string[];
  issuedAt: string;
  expiresAt: string;
}

export interface LoginSubmission {
  displayName: string;
  email: string;
  workspaceId: string;
  role: WorkspaceRole;
}

export interface SignupSubmission {
  displayName: string;
  email: string;
  workspaceName: string;
  role: WorkspaceRole;
}

export interface AuthRequestEnvelope {
  next?: string;
}

export interface RoleProfile {
  label: string;
  summary: string;
  tone: "success" | "warning" | "info" | "muted";
  permissions: string[];
  routes: WorkspaceRoute[];
}

export interface RoleOption {
  value: WorkspaceRole;
  label: string;
  summary: string;
  tone: RoleProfile["tone"];
}

export const AUTH_COOKIE_NAME = "nexusai_session";
export const SESSION_MAX_AGE_SECONDS = 60 * 60 * 8;

export const ROLE_PROFILES: Record<WorkspaceRole, RoleProfile> = {
  owner: {
    label: "Owner",
    summary: "Full workspace control with access to every review surface.",
    tone: "success",
    permissions: [
      "workspace:read",
      "workspace:manage",
      "telemetry:read",
      "telemetry:write",
      "analysis:read",
      "analysis:write",
      "evidence:read",
      "incident:manage",
      "summary:write",
      "alerts:read",
    ],
    routes: ["/", "/alerts", "/findings", "/incidents", "/graph", "/postmortems", "/finops"],
  },
  incident_commander: {
    label: "Incident commander",
    summary: "Keeps incidents moving, aligns responders, and closes the loop.",
    tone: "warning",
    permissions: [
      "workspace:read",
      "telemetry:read",
      "analysis:read",
      "analysis:write",
      "evidence:read",
      "incident:manage",
      "summary:write",
      "alerts:read",
    ],
    routes: ["/", "/alerts", "/findings", "/incidents", "/graph", "/postmortems", "/finops"],
  },
  analyst: {
    label: "Analyst",
    summary: "Focuses on evidence, correlations, and the shape of the story.",
    tone: "info",
    permissions: ["workspace:read", "telemetry:read", "analysis:read", "evidence:read", "summary:write", "alerts:read"],
    routes: ["/", "/alerts", "/findings", "/graph", "/postmortems", "/finops"],
  },
  service_owner: {
    label: "Service owner",
    summary: "Tracks service impact and helps turn findings into action.",
    tone: "warning",
    permissions: ["workspace:read", "telemetry:read", "analysis:read", "evidence:read", "incident:read", "summary:write", "alerts:read"],
    routes: ["/", "/alerts", "/findings", "/incidents", "/postmortems", "/finops"],
  },
  viewer: {
    label: "Viewer",
    summary: "Read-only access for review, sharing, and oversight.",
    tone: "muted",
    permissions: ["workspace:read", "telemetry:read", "analysis:read", "evidence:read", "alerts:read"],
    routes: ["/", "/alerts", "/findings", "/finops"],
  },
};

export const ROLE_OPTIONS: RoleOption[] = (Object.entries(ROLE_PROFILES) as Array<[WorkspaceRole, RoleProfile]>).map(
  ([value, profile]) => ({
    value,
    label: profile.label,
    summary: profile.summary,
    tone: profile.tone,
  }),
);

export const DASHBOARD_ROUTES: Array<{ href: WorkspaceRoute; label: string }> = [
  { href: "/", label: "Overview" },
  { href: "/alerts", label: "Alerts" },
  { href: "/findings", label: "Findings" },
  { href: "/incidents", label: "Incidents" },
  { href: "/graph", label: "Graph" },
  { href: "/postmortems", label: "Postmortems" },
  { href: "/finops", label: "FinOps" },
];

export function isWorkspaceRole(value: string): value is WorkspaceRole {
  return value in ROLE_PROFILES;
}

export function getRoleProfile(role: WorkspaceRole): RoleProfile {
  return ROLE_PROFILES[role];
}

export function getRoleOptions(): RoleOption[] {
  return ROLE_OPTIONS;
}

export function getAccessibleRoutes(role: WorkspaceRole | null | undefined): Array<{ href: WorkspaceRoute; label: string }> {
  if (!role) {
    return DASHBOARD_ROUTES;
  }

  const profile = getRoleProfile(role);
  return DASHBOARD_ROUTES.filter((route) => profile.routes.includes(route.href));
}

export function normalizeTenantSlug(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/['".]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

export function formatTenantLabel(value: string): string {
  const normalized = value
    .trim()
    .replace(/[-_]+/g, " ")
    .replace(/\s+/g, " ");

  if (!normalized) {
    return "Workspace";
  }

  return normalized.replace(/\b\w/g, (character) => character.toUpperCase());
}

export function sanitizeNextPath(value: string | null | undefined, fallback = "/"): string {
  if (!value) {
    return fallback;
  }

  const trimmed = value.trim();
  if (!trimmed.startsWith("/") || trimmed.startsWith("//")) {
    return fallback;
  }

  return trimmed;
}

export function buildUserId(tenantId: string, email: string): string {
  return `${normalizeTenantSlug(tenantId)}:${email.trim().toLowerCase()}`;
}
