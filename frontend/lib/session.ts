/** Server-side session helpers used by app routes and layouts. */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AUTH_COOKIE_NAME, type AuthSession } from "@/lib/auth";
import { decodeSessionCookie } from "@/lib/auth-server";

export async function getCurrentSession(): Promise<AuthSession | null> {
  const cookieStore = await cookies();
  return decodeSessionCookie(cookieStore.get(AUTH_COOKIE_NAME)?.value ?? null);
}

export async function requireCurrentSession(nextPath: string): Promise<AuthSession> {
  const session = await getCurrentSession();
  if (!session) {
    redirect(`/login?next=${encodeURIComponent(nextPath)}`);
  }

  return session;
}
