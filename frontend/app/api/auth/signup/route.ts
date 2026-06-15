import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME, sanitizeNextPath, type SignupSubmission, isWorkspaceRole } from "@/lib/auth";
import { createSignupSession, encodeSessionCookie, getSessionCookieOptions } from "@/lib/auth-server";

function parseSignupSubmission(body: unknown): SignupSubmission | null {
  if (!body || typeof body !== "object") {
    return null;
  }

  const record = body as Record<string, unknown>;
  const displayName = typeof record.displayName === "string" ? record.displayName.trim() : "";
  const email = typeof record.email === "string" ? record.email.trim() : "";
  const workspaceName = typeof record.workspaceName === "string" ? record.workspaceName.trim() : "";
  const role = typeof record.role === "string" && isWorkspaceRole(record.role) ? record.role : null;

  if (!displayName || !email || !workspaceName || !role) {
    return null;
  }

  return {
    displayName,
    email,
    workspaceName,
    role,
  };
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as unknown;
  const submission = parseSignupSubmission(body);
  if (!submission) {
    return NextResponse.json({ error: "Please fill in every field." }, { status: 400 });
  }

  const session = createSignupSession(submission);
  const nextPath = sanitizeNextPath((body as Record<string, unknown> | null)?.next as string | undefined, "/");
  const response = NextResponse.json({ next: nextPath, session: { tenantName: session.tenantName, role: session.role } });
  response.cookies.set(AUTH_COOKIE_NAME, encodeSessionCookie(session), getSessionCookieOptions());
  return response;
}
