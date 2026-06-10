import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME, sanitizeNextPath, type LoginSubmission, isWorkspaceRole } from "@/lib/auth";
import { createLoginSession, encodeSessionCookie, getSessionCookieOptions } from "@/lib/auth-server";

function parseLoginSubmission(body: unknown): LoginSubmission | null {
  if (!body || typeof body !== "object") {
    return null;
  }

  const record = body as Record<string, unknown>;
  const displayName = typeof record.displayName === "string" ? record.displayName.trim() : "";
  const email = typeof record.email === "string" ? record.email.trim() : "";
  const workspaceId = typeof record.workspaceId === "string" ? record.workspaceId.trim() : "";
  const role = typeof record.role === "string" && isWorkspaceRole(record.role) ? record.role : null;

  if (!displayName || !email || !workspaceId || !role) {
    return null;
  }

  return {
    displayName,
    email,
    workspaceId,
    role,
  };
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as unknown;
  const submission = parseLoginSubmission(body);
  if (!submission) {
    return NextResponse.json({ error: "Please fill in every field." }, { status: 400 });
  }

  const session = createLoginSession(submission);
  const nextPath = sanitizeNextPath((body as Record<string, unknown> | null)?.next as string | undefined, "/");
  const response = NextResponse.json({ next: nextPath, session: { tenantName: session.tenantName, role: session.role } });
  response.cookies.set(AUTH_COOKIE_NAME, encodeSessionCookie(session), getSessionCookieOptions());
  return response;
}
