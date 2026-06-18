"use client";

import { useEffect, useRef, useState } from "react";
import type { CSSProperties, PointerEvent as ReactPointerEvent, ReactNode } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { BrandMark } from "@/components/brand-mark";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getAccessibleRoutes, getRoleProfile, type AuthSession } from "@/lib/auth";
import { cn } from "@/lib/utils";
import {
  resolveSurfaceMode,
  sanitizeSurfacePreference,
  SURFACE_STORAGE_KEY,
  type SurfaceMode,
  type SurfacePreference,
} from "@/lib/theme";

interface AppShellProps {
  children: ReactNode;
  session: AuthSession | null;
}

function SurfaceToggle({
  preference,
  mode,
  onChange,
}: {
  preference: SurfacePreference;
  mode: SurfaceMode;
  onChange: (nextMode: SurfacePreference) => void;
}) {
  const shellClasses =
    mode === "light"
      ? "border-slate-200/80 bg-white/85 text-slate-900 shadow-[0_10px_30px_rgba(15,23,42,0.08)]"
      : "border-border/70 bg-background/80 text-foreground shadow-sm";
  const inactiveButtonClasses =
    mode === "light" ? "text-slate-500 hover:text-slate-900" : "text-muted-foreground hover:text-foreground";

  return (
    <div className={cn("inline-grid grid-cols-3 items-center gap-1 rounded-full p-1 backdrop-blur", shellClasses)}>
      {[
        ["system", "System"],
        ["dark", "Dark"],
        ["light", "Light"],
      ].map(([value, label]) => {
        const active = preference === value;
        return (
          <button
            key={value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(value as SurfacePreference)}
            className={cn(
              "rounded-full px-2.5 py-2 text-[10px] font-semibold uppercase tracking-[0.18em] transition sm:px-3 sm:text-xs",
              active ? "bg-primary text-primary-foreground" : inactiveButtonClasses,
            )}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}

function getPointerStyle(): CSSProperties {
  return {
    "--pointer-x": "50vw",
    "--pointer-y": "18vh",
  } as CSSProperties;
}

export function AppShell({ children, session }: AppShellProps) {
  const pathname = usePathname();
  const shellRef = useRef<HTMLDivElement | null>(null);
  const [surfacePreference, setSurfacePreference] = useState<SurfacePreference>("system");
  const [surfaceMode, setSurfaceMode] = useState<SurfaceMode>("dark");
  const [loggingOut, setLoggingOut] = useState(false);
  const authRoute = pathname.startsWith("/login") || pathname.startsWith("/signup");
  const visibleNavigation = getAccessibleRoutes(session?.role);
  const roleProfile = session ? getRoleProfile(session.role) : null;

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(SURFACE_STORAGE_KEY);
      setSurfacePreference(sanitizeSurfacePreference(stored));
    } catch {
      setSurfacePreference("system");
    }
  }, []);

  useEffect(() => {
    const systemQuery = window.matchMedia("(prefers-color-scheme: light)");

    function updateResolvedMode() {
      setSurfaceMode(resolveSurfaceMode(surfacePreference, systemQuery.matches));
    }

    updateResolvedMode();

    if (surfacePreference !== "system") {
      return;
    }

    systemQuery.addEventListener("change", updateResolvedMode);
    return () => systemQuery.removeEventListener("change", updateResolvedMode);
  }, [surfacePreference]);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.surfacePreference = surfacePreference;
    root.dataset.surface = surfaceMode;
    root.style.colorScheme = surfaceMode;

    try {
      window.localStorage.setItem(SURFACE_STORAGE_KEY, surfacePreference);
    } catch {
      // Ignore storage failures in locked-down environments.
    }
  }, [surfaceMode, surfacePreference]);

  function updatePointerPosition(event: ReactPointerEvent<HTMLDivElement>) {
    const shell = shellRef.current;
    if (!shell) {
      return;
    }

    shell.style.setProperty("--pointer-x", `${event.clientX}px`);
    shell.style.setProperty("--pointer-y", `${event.clientY}px`);
  }

  function resetPointerPosition() {
    const shell = shellRef.current;
    if (!shell) {
      return;
    }

    shell.style.setProperty("--pointer-x", "50vw");
    shell.style.setProperty("--pointer-y", "18vh");
  }

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
      <div
        ref={shellRef}
        data-surface={surfaceMode}
        onPointerMove={updatePointerPosition}
        onPointerLeave={resetPointerPosition}
        className="dashboard-shell relative min-h-screen overflow-hidden"
        style={getPointerStyle()}
      >
        <div className="workspace-grid pointer-events-none absolute inset-0" />
        <div className="workspace-glow pointer-events-none absolute inset-0" />
        <div className="noise-overlay pointer-events-none absolute inset-0" />
        <div className="relative mx-auto grid min-h-screen w-full max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[0.95fr,1.05fr] lg:px-8">
          <aside className="hidden flex-col justify-between rounded-[2.25rem] border border-white/8 bg-black/30 p-8 backdrop-blur-xl lg:flex">
            <div>
              <div className="flex items-start justify-between gap-4">
                <BrandMark />
                <SurfaceToggle preference={surfacePreference} mode={surfaceMode} onChange={setSurfacePreference} />
              </div>
              <p className="mt-8 text-xs uppercase tracking-[0.24em] text-muted-foreground">Workspace access</p>
              <h1 className="mt-3 max-w-md text-3xl font-semibold tracking-tight text-white">Open the right tenant and move faster.</h1>
              <p className="mt-4 max-w-md text-sm leading-7 text-muted-foreground">
                See the right scope first, then move from evidence to action with less noise.
              </p>
            </div>

            <div className="grid gap-3">
              <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                <p className="text-sm font-semibold text-white">Separate workspaces</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">Each tenant keeps its own context and access.</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                <p className="text-sm font-semibold text-white">Role-aware views</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">Each role sees the surfaces that matter most.</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                <p className="text-sm font-semibold text-white">Evidence first</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">Findings, incidents, and summaries stay linked.</p>
              </div>
            </div>
          </aside>

          <div className="flex items-center justify-center py-4">{children}</div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={shellRef}
      data-surface={surfaceMode}
      onPointerMove={updatePointerPosition}
      onPointerLeave={resetPointerPosition}
      className="dashboard-shell relative min-h-screen overflow-hidden"
      style={getPointerStyle()}
    >
      <div className="workspace-grid pointer-events-none absolute inset-0" />
      <div className="workspace-glow pointer-events-none absolute inset-0" />
      <div className="noise-overlay pointer-events-none absolute inset-0" />
      <div className="relative flex min-h-screen">
        <aside className="hidden w-[280px] shrink-0 border-r border-white/8 bg-black/20 px-5 py-6 backdrop-blur-xl lg:flex lg:flex-col">
          <div className="flex items-start justify-between gap-3">
            <BrandMark />
            <div className="hidden xl:block">
              <SurfaceToggle preference={surfacePreference} mode={surfaceMode} onChange={setSurfacePreference} />
            </div>
          </div>
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
            <p className="mt-2 text-sm leading-6 text-muted-foreground">Keep the evidence clear and the next step obvious.</p>
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
                  <p className="text-sm text-muted-foreground">Review evidence and keep the next step clear.</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <SurfaceToggle preference={surfacePreference} mode={surfaceMode} onChange={setSurfacePreference} />
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
