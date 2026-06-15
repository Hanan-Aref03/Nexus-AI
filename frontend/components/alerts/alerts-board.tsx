"use client";

import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { formatConfidence, formatDateTime, formatRelativeTime, titleCase } from "@/lib/format";
import type { AlertKind, AlertsFeed, TelemetrySeverity, WorkspaceAlert } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AlertsBoardProps {
  feed: AlertsFeed;
}

const severityFilters: Array<"all" | "critical" | "warning" | "info"> = ["all", "critical", "warning", "info"];
const kindFilters: Array<"all" | AlertKind> = ["all", "incident", "health"];

function severityTone(severity: TelemetrySeverity): "success" | "warning" | "danger" | "info" | "muted" {
  switch (severity) {
    case "critical":
      return "danger";
    case "warning":
      return "warning";
    case "info":
      return "info";
    default:
      return "muted";
  }
}

function alertKindTone(kind: AlertKind): "danger" | "info" {
  return kind === "incident" ? "danger" : "info";
}

function matchesQuery(alert: WorkspaceAlert, query: string): boolean {
  if (!query.trim()) {
    return true;
  }

  const needle = query.toLowerCase();
  return [alert.title, alert.summary, alert.scopeName, alert.sourceLabel, alert.sourceDetail, ...alert.tags]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(needle));
}

export function AlertsBoard({ feed }: AlertsBoardProps) {
  const [kindFilter, setKindFilter] = useState<"all" | AlertKind>("all");
  const [severityFilter, setSeverityFilter] = useState<"all" | "critical" | "warning" | "info">("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(feed.alerts[0]?.id ?? "");

  const visibleAlerts = useMemo(
    () =>
      feed.alerts.filter((alert) => {
        const matchesKind = kindFilter === "all" || alert.kind === kindFilter;
        const matchesSeverity = severityFilter === "all" || alert.severity === severityFilter;
        return matchesKind && matchesSeverity && matchesQuery(alert, query);
      }),
    [feed.alerts, kindFilter, query, severityFilter],
  );

  const hasVisibleAlerts = visibleAlerts.length > 0;
  const selectedAlert = hasVisibleAlerts ? visibleAlerts.find((alert) => alert.id === selectedId) ?? visibleAlerts[0] ?? null : null;
  const selectedAlertId = selectedAlert?.id ?? "";

  if (feed.alerts.length === 0) {
    return (
      <Card>
        <CardBody className="p-8 text-sm leading-6 text-muted-foreground">{feed.sourceReason}</CardBody>
      </Card>
    );
  }

  function resetFilters() {
    setKindFilter("all");
    setSeverityFilter("all");
    setQuery("");
    setSelectedId(feed.alerts[0]?.id ?? "");
  }

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Alert inbox</p>
            <CardTitle className="mt-1">Respond faster with a single evidence-backed queue</CardTitle>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge tone={feed.summary.critical > 0 ? "danger" : "info"}>{feed.summary.critical} critical</Badge>
            <Badge tone="muted">{visibleAlerts.length} visible</Badge>
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-[1.2fr,0.8fr]">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search title, scope, or tag..."
            className="h-11 w-full rounded-full border border-white/10 bg-black/20 px-4 text-sm text-white outline-none placeholder:text-muted-foreground focus:border-primary/40 focus:ring-2 focus:ring-primary/20"
          />
          <div className="flex flex-wrap gap-2 lg:justify-end">
            {kindFilters.map((option) => (
              <Button
                key={option}
                size="sm"
                variant={kindFilter === option ? "primary" : "outline"}
                onClick={() => setKindFilter(option)}
              >
                {option === "all" ? "All alerts" : titleCase(option)}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {severityFilters.map((option) => (
            <Button
              key={option}
              size="sm"
              variant={severityFilter === option ? "primary" : "outline"}
              onClick={() => setSeverityFilter(option)}
            >
              {option === "all" ? "Any severity" : titleCase(option)}
            </Button>
          ))}
        </div>
      </CardHeader>

      <CardBody className="grid gap-5 xl:grid-cols-[0.95fr,1.05fr]">
        <div className="space-y-3">
          {!hasVisibleAlerts ? (
            <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-8 text-sm leading-6 text-muted-foreground">
              <p>No alerts match the current filters. Try a broader search or switch back to all severities.</p>
              <Button variant="outline" size="sm" className="mt-4" onClick={resetFilters}>
                Clear filters
              </Button>
            </div>
          ) : (
            visibleAlerts.map((alert) => (
              <button
                key={alert.id}
                onClick={() => setSelectedId(alert.id)}
                className={cn(
                  "w-full rounded-3xl border p-4 text-left transition-all duration-200",
                  alert.id === selectedAlertId
                    ? "border-primary/40 bg-primary/10"
                    : "border-white/8 bg-white/5 hover:border-white/12 hover:bg-white/8",
                )}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap gap-2">
                    <Badge tone={severityTone(alert.severity)}>{alert.severity}</Badge>
                    <Badge tone={alertKindTone(alert.kind)}>{alert.kind}</Badge>
                  </div>
                  <span className="text-xs text-muted-foreground">{formatRelativeTime(alert.updatedAt)}</span>
                </div>
                <h3 className="mt-3 text-base font-semibold text-white">{alert.title}</h3>
                <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">{alert.summary}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-muted-foreground">
                    {alert.sourceLabel}
                  </span>
                  <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-muted-foreground">
                    {alert.sourceDetail}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>

        <div className="space-y-4 rounded-3xl border border-white/8 bg-black/20 p-5">
          {!selectedAlert ? (
            <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-8 text-sm leading-6 text-muted-foreground">
              No alert is selected. Reset the filters to bring the queue back into view.
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Selected alert</p>
                  <h3 className="mt-2 text-2xl font-semibold tracking-tight text-white">{selectedAlert.title}</h3>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{selectedAlert.summary}</p>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-3 text-right">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Updated</p>
                  <p className="mt-2 text-sm font-semibold text-white">{formatDateTime(selectedAlert.updatedAt)}</p>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Confidence</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{formatConfidence(selectedAlert.confidence)}</p>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Evidence</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{selectedAlert.evidenceCount}</p>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Scope</p>
                  <p className="mt-2 text-sm font-semibold text-white">
                    {titleCase(selectedAlert.scopeKind)} {selectedAlert.scopeName}
                  </p>
                </div>
              </div>

              <div className="grid gap-4 lg:grid-cols-[1fr,0.9fr]">
                <div className="rounded-3xl border border-white/8 bg-white/5 p-4">
                  <p className="text-sm font-semibold text-white">Details</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {selectedAlert.tags.map((tag) => (
                      <Badge key={tag} tone={tag === "security" ? "danger" : "muted"}>
                        {tag}
                      </Badge>
                    ))}
                  </div>

                  <dl className="mt-4 grid gap-3 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <dt className="text-muted-foreground">Source</dt>
                      <dd className="font-medium text-white">{selectedAlert.sourceLabel}</dd>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <dt className="text-muted-foreground">Context</dt>
                      <dd className="font-medium text-white">{selectedAlert.sourceDetail}</dd>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <dt className="text-muted-foreground">Action</dt>
                      <dd className="font-medium text-white">{selectedAlert.actionLabel}</dd>
                    </div>
                  </dl>

                  <Button href={selectedAlert.href} className="mt-5 w-full">
                    {selectedAlert.actionLabel}
                  </Button>
                </div>

                <div className="space-y-4">
                  <div className="rounded-3xl border border-white/8 bg-white/5 p-4">
                    <p className="text-sm font-semibold text-white">Copilot prompt</p>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">{feed.copilotPrompt}</p>
                  </div>

                  <div className="rounded-3xl border border-white/8 bg-white/5 p-4">
                    <p className="text-sm font-semibold text-white">Slack preview</p>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">{feed.slackPreview}</p>
                  </div>

                  <div className="rounded-3xl border border-white/8 bg-white/5 p-4">
                    <p className="text-sm font-semibold text-white">Workspace source</p>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">{feed.sourceReason}</p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <Badge tone="info">{feed.sourceLabel}</Badge>
                      <Badge tone="muted">Generated {formatDateTime(feed.generatedAt)}</Badge>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
