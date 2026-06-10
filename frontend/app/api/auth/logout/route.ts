import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME } from "@/lib/auth";
import { getSessionCookieOptions } from "@/lib/auth-server";

export async function POST() {
  const response = NextResponse.json({ next: "/login" });
  response.cookies.set(AUTH_COOKIE_NAME, "", {
    ...getSessionCookieOptions(),
    maxAge: 0,
  });
  return response;
}
