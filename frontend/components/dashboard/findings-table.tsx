"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { formatConfidence, formatDateTime, titleCase } from "@/lib/format";
import type { AnalysisFinding, TelemetrySeverity } from "@/lib/types";

interface FindingsTableProps {
  findings: AnalysisFinding[];
}

const severityOptions: Array<"all" | TelemetrySeverity> = ["all", "critical", "error", "warning", "info", "debug"];

export function FindingsTable({ findings }: FindingsTableProps) {
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState<"all" | TelemetrySeverity>("all");

  const filteredFindings = findings.filter((finding) => {
    const matchesQuery =
      query.trim().length === 0 ||
      [finding.title, finding.summary, finding.service_name, finding.workload_name, finding.namespace]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query.toLowerCase()));
    const matchesSeverity = severity === "all" || finding.severity === severity;
    return matchesQuery && matchesSeverity;
  });

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Findings</p>
            <CardTitle className="mt-1">Key evidence</CardTitle>
          </div>
          <Badge tone="muted">{filteredFindings.length} visible</Badge>
        </div>

        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search title, service, or namespace..."
            className="h-11 w-full rounded-full border border-white/10 bg-black/20 px-4 text-sm text-white outline-none placeholder:text-muted-foreground focus:border-primary/40 focus:ring-2 focus:ring-primary/20 lg:max-w-xl"
          />
          <div className="flex flex-wrap gap-2">
            {severityOptions.map((option) => (
              <Button
                key={option}
                variant={severity === option ? "primary" : "outline"}
                size="sm"
                onClick={() => setSeverity(option)}
              >
                {option === "all" ? "All" : titleCase(option)}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>

      <CardBody className="space-y-3">
        {filteredFindings.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-8 text-sm text-muted-foreground">
            No findings match the current filter. Try a broader query or clear the severity filter.
          </div>
        ) : (
          filteredFindings.map((finding) => (
            <article
              key={finding.id}
              className="grid gap-4 rounded-3xl border border-white/8 bg-white/5 p-4 lg:grid-cols-[1.4fr,0.8fr]"
            >
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="info">{titleCase(finding.category)}</Badge>
                  <Badge tone="muted">{titleCase(finding.source_type)}</Badge>
                  <Badge tone="muted">{finding.kind}</Badge>
                </div>
                <h3 className="mt-3 text-lg font-semibold text-white">{finding.title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{finding.summary}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {finding.recommendations.slice(0, 3).map((item) => (
                    <span key={item} className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-muted-foreground">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
                <div className="flex items-center justify-between gap-3">
                  <Badge
                    tone={
                      finding.severity === "critical"
                        ? "danger"
                        : finding.severity === "error"
                          ? "danger"
                          : finding.severity === "warning"
                            ? "warning"
                            : finding.severity === "info"
                              ? "info"
                              : "muted"
                    }
                  >
                    {finding.severity}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{formatDateTime(finding.observed_at)}</span>
                </div>

                <dl className="mt-4 grid gap-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <dt className="text-muted-foreground">Confidence</dt>
                    <dd className="font-medium text-white">{formatConfidence(finding.confidence)}</dd>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <dt className="text-muted-foreground">Service</dt>
                    <dd className="font-medium text-white">{finding.service_name ?? finding.workload_name ?? "n/a"}</dd>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <dt className="text-muted-foreground">Workload</dt>
                    <dd className="font-medium text-white">{finding.workload_name ?? "n/a"}</dd>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <dt className="text-muted-foreground">Namespace</dt>
                    <dd className="font-medium text-white">{finding.namespace ?? "n/a"}</dd>
                  </div>
                </dl>
              </div>
            </article>
          ))
        )}
      </CardBody>
    </Card>
  );
}
