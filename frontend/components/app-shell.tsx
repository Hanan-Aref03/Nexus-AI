"use client";

import type { ReactNode } from "react";
import { useState } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { BrandMark } from "@/components/brand-mark";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getAccessibleRoutes, getRoleProfile, type AuthSession } from "@/lib/auth";
import { cn } from "@/lib/utils";

interface AppShellProps {
  children: ReactNode;
  session: AuthSession | null;
}

export function AppShell({ children, session }: AppShellProps) {
  const pathname = usePathname();
  const [loggingOut, setLoggingOut] = useState(false);
  const authRoute = pathname.startsWith("/login") || pathname.startsWith("/signup");
  const visibleNavigation = getAccessibleRoutes(session?.role);
  const roleProfile = session ? getRoleProfile(session.role) : null;

  async function handleLogout() {
    setLoggingOut(true);

    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      window.location.assign("/login");
    }
  }

  if (authRoute) {
    return (
      <div className="dashboard-shell relative min-h-screen overflow-hidden bg-grid-radial">
        <div className="noise-overlay pointer-events-none absolute inset-0" />
        <div className="relative mx-auto grid min-h-screen w-full max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[0.95fr,1.05fr] lg:px-8">
          <aside className="hidden flex-col justify-between rounded-[2.25rem] border border-white/8 bg-black/30 p-8 backdrop-blur-xl lg:flex">
            <div>
              <BrandMark />
              <p className="mt-8 text-xs uppercase tracking-[0.24em] text-muted-foreground">Workspace access</p>
              <h1 className="mt-3 max-w-md text-3xl font-semibold tracking-tight text-white">
                Keep each tenant separate and every role easy to understand.
              </h1>
              <p className="mt-4 max-w-md text-sm leading-7 text-muted-foreground">
                Open the workspace with the right identity, see the right scope first, and move from evidence to decision without friction.
              </p>
            </div>

            <div className="grid gap-3">
              <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                <p className="text-sm font-semibold text-white">Separate workspaces</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">Each tenant keeps its own context, access, and review flow.</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                <p className="text-sm font-semibold text-white">Role-aware views</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">Owners, analysts, and responders each see the surfaces that matter most.</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                <p className="text-sm font-semibold text-white">Evidence first</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">Findings, incidents, and summaries stay connected from the start.</p>
              </div>
            </div>
          </aside>

          <div className="flex items-center justify-center py-4">{children}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-shell relative min-h-screen overflow-hidden bg-grid-radial">
      <div className="noise-overlay pointer-events-none absolute inset-0" />
      <div className="relative flex min-h-screen">
        <aside className="hidden w-[280px] shrink-0 border-r border-white/8 bg-black/20 px-5 py-6 backdrop-blur-xl lg:flex lg:flex-col">
          <BrandMark />
          <div className="mt-8 rounded-3xl border border-white/8 bg-white/5 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Workspace</p>
                <p className="mt-1 text-lg font-semibold text-white">{session?.tenantName ?? "NexusAI"}</p>
              </div>
              <Badge tone={session ? roleProfile?.tone ?? "info" : "muted"}>{session ? roleProfile?.label : "Guest"}</Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              {session
                ? `${session.displayName} is signed in for ${session.tenantName}.`
                : "Sign in to open the workspace and review the current evidence."}
            </p>
          </div>

          <nav className="mt-8 space-y-2">
            {visibleNavigation.map((item) => {
              const active = item.href === "/" ? pathname === item.href : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href as any}
                  className={cn(
                    "flex items-center justify-between rounded-2xl border px-4 py-3 text-sm font-medium transition-all",
                    active
                      ? "border-primary/30 bg-primary/10 text-white shadow-[0_0_0_1px_rgba(45,212,191,0.12)]"
                      : "border-transparent text-muted-foreground hover:border-white/8 hover:bg-white/5 hover:text-white",
                  )}
                >
                  <span>{item.label}</span>
                  {active ? <span className="h-2 w-2 rounded-full bg-primary" /> : null}
                </Link>
              );
            })}
          </nav>

          <div className="mt-auto rounded-3xl border border-white/8 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Focus</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Keep the evidence visible, the scope clear, and the next step obvious for every review.
            </p>
            {session ? (
              <Button variant="secondary" size="sm" className="mt-4 w-full" onClick={handleLogout} disabled={loggingOut}>
                {loggingOut ? "Signing out..." : "Sign out"}
              </Button>
            ) : (
              <Button href="/login" variant="secondary" size="sm" className="mt-4 w-full">
                Sign in
              </Button>
            )}
          </div>
        </aside>

        <div className="flex min-h-screen flex-1 flex-col">
          <header className="sticky top-0 z-30 border-b border-white/8 bg-black/30 backdrop-blur-xl">
            <div className="flex items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
              <div className="flex items-center gap-4">
                <div className="lg:hidden">
                  <BrandMark compact />
                </div>
                <div className="hidden lg:block">
                  <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">NexusAI workspace</p>
                  <p className="text-sm text-muted-foreground">Review evidence, coordinate responses, and keep the summary concise.</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {session ? (
                  <>
                    <Badge tone="info">{session.tenantName}</Badge>
                    <Badge tone={roleProfile?.tone ?? "muted"}>{roleProfile?.label}</Badge>
                    <Button variant="secondary" size="sm" onClick={handleLogout} disabled={loggingOut}>
                      {loggingOut ? "Signing out..." : "Sign out"}
                    </Button>
                  </>
                ) : (
                  <>
                    <Badge tone="success">Tenant aware</Badge>
                    <Badge tone="info">Evidence first</Badge>
                    <Button href="/login" variant="secondary" size="sm">
                      Sign in
                    </Button>
                  </>
                )}
              </div>
            </div>

            <div className="flex gap-2 overflow-x-auto px-4 pb-4 sm:px-6 lg:hidden">
              {visibleNavigation.map((item) => {
                const active = item.href === "/" ? pathname === item.href : pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href as any}
                    className={cn(
                      "whitespace-nowrap rounded-full border px-4 py-2 text-sm transition-all",
                      active
                        ? "border-primary/30 bg-primary/10 text-white"
                        : "border-white/8 bg-white/5 text-muted-foreground",
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </header>

          <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
            <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
