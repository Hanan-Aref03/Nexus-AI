/** Formatting helpers used across the workspace UI. */

import type { AnalysisHealthStatus, AnalysisIncidentState, TelemetrySeverity } from "@/lib/types";

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "n/a";
  }

  const date = new Date(value);
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) {
    return "n/a";
  }

  const date = new Date(value);
  const deltaMs = date.getTime() - Date.now();
  const deltaMinutes = Math.round(deltaMs / 60000);
  const deltaHours = Math.round(deltaMs / 3600000);

  if (Math.abs(deltaMinutes) < 60) {
    return `${Math.abs(deltaMinutes)}m ${deltaMinutes <= 0 ? "ago" : "from now"}`;
  }

  return `${Math.abs(deltaHours)}h ${deltaHours <= 0 ? "ago" : "from now"}`;
}

export function formatScore(value: number): string {
  return `${Math.round(value)}`;
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}% confidence`;
}

export function titleCase(value: string): string {
  return value
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function severityTone(severity: TelemetrySeverity): string {
  switch (severity) {
    case "critical":
      return "border-rose-500/40 bg-rose-500/10 text-rose-200";
    case "error":
      return "border-orange-500/40 bg-orange-500/10 text-orange-100";
    case "warning":
      return "border-amber-500/40 bg-amber-500/10 text-amber-100";
    case "info":
      return "border-cyan-500/40 bg-cyan-500/10 text-cyan-100";
    default:
      return "border-slate-500/40 bg-slate-500/10 text-slate-100";
  }
}

export function stateTone(state: AnalysisIncidentState): string {
  switch (state) {
    case "resolved":
      return "border-emerald-500/40 bg-emerald-500/10 text-emerald-100";
    case "investigating":
      return "border-cyan-500/40 bg-cyan-500/10 text-cyan-100";
    case "acknowledged":
      return "border-amber-500/40 bg-amber-500/10 text-amber-100";
    default:
      return "border-rose-500/40 bg-rose-500/10 text-rose-100";
  }
}

export function healthTone(status: AnalysisHealthStatus | "stable"): string {
  switch (status) {
    case "critical":
      return "border-rose-500/40 bg-rose-500/10 text-rose-100";
    case "degraded":
      return "border-orange-500/40 bg-orange-500/10 text-orange-100";
    case "watch":
      return "border-amber-500/40 bg-amber-500/10 text-amber-100";
    case "healthy":
    case "stable":
      return "border-emerald-500/40 bg-emerald-500/10 text-emerald-100";
    default:
      return "border-slate-500/40 bg-slate-500/10 text-slate-100";
  }
}
