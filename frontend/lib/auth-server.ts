/** Server-only auth helpers for session cookies and backend access tokens. */

import { createHash, createHmac, randomUUID, timingSafeEqual } from "node:crypto";

import {
  AUTH_COOKIE_NAME,
  SESSION_MAX_AGE_SECONDS,
  formatTenantLabel,
  getRoleProfile,
  isWorkspaceRole,
  normalizeTenantSlug,
  type AuthSession,
  type LoginSubmission,
  type SignupSubmission,
} from "@/lib/auth";

function getAuthSigningKey(): string {
  return process.env.AUTH_SIGNING_KEY ?? "dev-only-change-me";
}

function getBackendAuthContext(session: AuthSession | null) {
  const issuedAt = Math.floor(Date.now() / 1000);

  if (session) {
    return {
      audience: process.env.AUTH_TOKEN_AUDIENCE ?? "nexusai-web",
      issuer: process.env.AUTH_TOKEN_ISSUER ?? "nexusai",
      tenantId: session.tenantId,
      subject: session.userId,
      roles: [session.role],
      permissions: session.permissions,
      email: session.email,
      displayName: session.displayName,
      issuedAt,
      expiresAt: issuedAt + 60 * 15,
    };
  }

  return {
    audience: process.env.AUTH_TOKEN_AUDIENCE ?? "nexusai-web",
    issuer: process.env.AUTH_TOKEN_ISSUER ?? "nexusai",
    tenantId: process.env.NEXUSAI_TENANT_ID ?? "platform-demo",
    subject: process.env.NEXUSAI_DEMO_SUBJECT ?? "frontend-investigator",
    roles: (process.env.NEXUSAI_DEMO_ROLES ?? "analysis:read,analysis:write")
      .split(",")
      .map((role) => role.trim())
      .filter(Boolean),
    permissions: ["workspace:read", "evidence:read"],
    email: "demo@nexusai.local",
    displayName: "Demo reviewer",
    issuedAt,
    expiresAt: issuedAt + 60 * 15,
  };
}

function toBase64Url(value: string): string {
  return Buffer.from(value).toString("base64url");
}

function fromBase64Url(value: string): string {
  return Buffer.from(value, "base64url").toString("utf8");
}

function signPayload(payload: string): string {
  return createHmac("sha256", getAuthSigningKey()).update(payload).digest("base64url");
}

function isSignatureValid(payload: string, signature: string): boolean {
  const expected = Buffer.from(signPayload(payload));
  const provided = Buffer.from(signature);

  if (expected.length !== provided.length) {
    return false;
  }

  return timingSafeEqual(expected, provided);
}

export function buildAuthSession(input: LoginSubmission | SignupSubmission): AuthSession {
  const now = new Date();
  const issuedAt = now.toISOString();
  const expiresAt = new Date(now.getTime() + SESSION_MAX_AGE_SECONDS * 1000).toISOString();
  const tenantId = "workspaceId" in input ? normalizeTenantSlug(input.workspaceId) : normalizeTenantSlug(input.workspaceName);
  const tenantName = "workspaceId" in input ? formatTenantLabel(input.workspaceId) : input.workspaceName.trim();
  const email = input.email.trim().toLowerCase();
  const displayName = input.displayName.trim();

  return {
    sessionId: randomUUID(),
    userId: createHash("sha256").update(`${tenantId}:${email}`).digest("hex").slice(0, 24),
    displayName,
    email,
    tenantId,
    tenantName,
    role: input.role,
    permissions: [...getRoleProfile(input.role).permissions],
    issuedAt,
    expiresAt,
  };
}

export function encodeSessionCookie(session: AuthSession): string {
  const payload = {
    sessionId: session.sessionId,
    userId: session.userId,
    displayName: session.displayName,
    email: session.email,
    tenantId: session.tenantId,
    tenantName: session.tenantName,
    role: session.role,
    permissions: session.permissions,
    issuedAt: session.issuedAt,
    expiresAt: session.expiresAt,
  };

  const encodedPayload = toBase64Url(JSON.stringify(payload));
  const signature = signPayload(encodedPayload);
  return `nexusai.session.${encodedPayload}.${signature}`;
}

export function decodeSessionCookie(value: string | null | undefined): AuthSession | null {
  if (!value) {
    return null;
  }

  const segments = value.split(".");
  if (segments.length !== 4 || segments[0] !== "nexusai" || segments[1] !== "session") {
    return null;
  }

  const payload = segments[2];
  const providedSignature = segments[3];
  if (!payload || !providedSignature || !isSignatureValid(payload, providedSignature)) {
    return null;
  }

  try {
    const decoded = JSON.parse(fromBase64Url(payload)) as AuthSession;
    if (
      typeof decoded.sessionId !== "string" ||
      typeof decoded.userId !== "string" ||
      typeof decoded.displayName !== "string" ||
      typeof decoded.email !== "string" ||
      typeof decoded.tenantId !== "string" ||
      typeof decoded.tenantName !== "string" ||
      typeof decoded.issuedAt !== "string" ||
      typeof decoded.expiresAt !== "string" ||
      !isWorkspaceRole(decoded.role)
    ) {
      return null;
    }

    if (Date.parse(decoded.expiresAt) <= Date.now()) {
      return null;
    }

    const permissions = Array.isArray(decoded.permissions)
      ? decoded.permissions.filter((permission): permission is string => typeof permission === "string")
      : [];

    return {
      ...decoded,
      permissions: permissions.length ? permissions : [...getRoleProfile(decoded.role).permissions],
    };
  } catch {
    return null;
  }
}

export function createLoginSession(input: LoginSubmission): AuthSession {
  const tenantId = normalizeTenantSlug(input.workspaceId);
  return {
    ...buildAuthSession({
      ...input,
      workspaceId: tenantId,
    }),
    tenantId,
    tenantName: formatTenantLabel(input.workspaceId),
  };
}

export function createSignupSession(input: SignupSubmission): AuthSession {
  return buildAuthSession(input);
}

export function createBackendAccessToken(session: AuthSession | null): string {
  const auth = getBackendAuthContext(session);
  const payload = {
    aud: auth.audience,
    exp: auth.expiresAt,
    iat: auth.issuedAt,
    iss: auth.issuer,
    permissions: auth.permissions,
    roles: auth.roles,
    sub: auth.subject,
    tenant_id: auth.tenantId,
    user_email: auth.email,
    user_name: auth.displayName,
  };

  const encodedPayload = toBase64Url(JSON.stringify(payload));
  const signature = signPayload(encodedPayload);
  return `nexusai.v1.${encodedPayload}.${signature}`;
}

export function getSessionCookieOptions(isProduction = process.env.NODE_ENV === "production") {
  return {
    httpOnly: true,
    maxAge: SESSION_MAX_AGE_SECONDS,
    path: "/",
    sameSite: "lax" as const,
    secure: isProduction,
  };
}

export { AUTH_COOKIE_NAME };
