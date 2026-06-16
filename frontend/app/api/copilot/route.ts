import { NextResponse } from "next/server";

import { createBackendAccessToken } from "@/lib/auth-server";
import { getCurrentSession } from "@/lib/session";

function getBackendBaseUrl(): string {
  return process.env.BACKEND_BASE_URL ?? process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
}

export async function POST(request: Request) {
  const session = await getCurrentSession();
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let payload: { question?: string } = {};
  try {
    payload = (await request.json()) as { question?: string };
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const question = payload.question?.trim();
  if (!question) {
    return NextResponse.json({ error: "A question is required." }, { status: 400 });
  }

  const response = await fetch(`${getBackendBaseUrl()}/api/v1/copilot/query`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${createBackendAccessToken(session)}`,
      "Content-Type": "application/json",
      "X-Tenant-Id": session.tenantId,
      "X-User-Role": session.role,
      "X-User-Email": session.email,
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    return NextResponse.json(
      { error: `Copilot request failed with status ${response.status}.` },
      { status: response.status },
    );
  }

  return NextResponse.json(await response.json());
}

