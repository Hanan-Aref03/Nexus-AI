"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { buildIncidentTimeline } from "@/lib/insights";
import { formatConfidence, formatDateTime, formatRelativeTime, titleCase } from "@/lib/format";
import type { AnalysisIncident, AnalysisIncidentState, AnalysisFinding } from "@/lib/types";

interface IncidentExplorerProps {
  incidents: AnalysisIncident[];
  findings: AnalysisFinding[];
}

const stateOptions: Array<"all" | AnalysisIncidentState> = ["all", "open", "acknowledged", "investigating", "resolved"];

export function IncidentExplorer({ incidents, findings }: IncidentExplorerProps) {
  const [stateFilter, setStateFilter] = useState<"all" | AnalysisIncidentState>("all");
  const [selectedId, setSelectedId] = useState(incidents[0]?.id ?? "");

  const visibleIncidents = incidents.filter((incident) => stateFilter === "all" || incident.state === stateFilter);
  const selectedIncident =
    visibleIncidents.find((incident) => incident.id === selectedId) ?? visibleIncidents[0] ?? incidents[0] ?? null;

  const evidenceFindings = selectedIncident ? findings.filter((finding) => finding.incident_id === selectedIncident.id) : [];

  if (!selectedIncident) {
    return (
      <Card>
        <CardBody className="p-8 text-sm text-muted-foreground">No incidents available yet.</CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Incidents</p>
            <CardTitle className="mt-1">Active incidents</CardTitle>
          </div>
          <Badge tone={selectedIncident.state === "resolved" ? "success" : selectedIncident.state === "investigating" ? "info" : "warning"}>
            {selectedIncident.state}
          </Badge>
        </div>

        <div className="flex flex-wrap gap-2">
          {stateOptions.map((option) => (
            <Button
              key={option}
              size="sm"
              variant={stateFilter === option ? "primary" : "outline"}
              onClick={() => {
                setStateFilter(option);
                const firstVisible = incidents.find((incident) => option === "all" || incident.state === option);
                if (firstVisible) {
                  setSelectedId(firstVisible.id);
                }
              }}
            >
              {option === "all" ? "All states" : titleCase(option)}
            </Button>
          ))}
        </div>
      </CardHeader>

      <CardBody className="grid gap-5 xl:grid-cols-[0.95fr,1.05fr]">
        <div className="space-y-3">
          {visibleIncidents.map((incident) => (
            <button
              key={incident.id}
              onClick={() => setSelectedId(incident.id)}
              className={`
                w-full rounded-3xl border p-4 text-left transition-all duration-200
                ${incident.id === selectedIncident.id ? "border-primary/40 bg-primary/10" : "border-white/8 bg-white/5 hover:bg-white/8"}
              `}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Badge tone={incident.state === "resolved" ? "success" : incident.state === "investigating" ? "info" : "warning"}>
                  {incident.state}
                </Badge>
                <span className="text-xs text-muted-foreground">{formatRelativeTime(incident.updated_at)}</span>
              </div>
              <h3 className="mt-3 text-base font-semibold text-white">{incident.title}</h3>
              <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">{incident.summary}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-muted-foreground">
                  {incident.scope_kind}: {incident.scope_name}
                </span>
                <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-muted-foreground">
                  {formatConfidence(incident.confidence)}
                </span>
              </div>
            </button>
          ))}
        </div>

        <div className="space-y-4 rounded-3xl border border-white/8 bg-black/20 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Selected incident</p>
              <h3 className="mt-2 text-2xl font-semibold tracking-tight text-white">{selectedIncident.title}</h3>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{selectedIncident.summary}</p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/5 p-3 text-right">
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Updated</p>
              <p className="mt-2 text-sm font-semibold text-white">{formatDateTime(selectedIncident.updated_at)}</p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Confidence</p>
              <p className="mt-2 text-2xl font-semibold text-white">{formatConfidence(selectedIncident.confidence)}</p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Evidence</p>
              <p className="mt-2 text-2xl font-semibold text-white">{selectedIncident.evidence_count}</p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">State</p>
              <p className="mt-2 text-2xl font-semibold text-white">{titleCase(selectedIncident.state)}</p>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1fr,0.9fr]">
          <div className="rounded-3xl border border-white/8 bg-white/5 p-4">
            <p className="text-sm font-semibold text-white">Probable cause</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{selectedIncident.probable_cause}</p>

              <div className="mt-4">
                <p className="text-sm font-semibold text-white">Recommendations</p>
                <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
                  {selectedIncident.recommendations.map((item) => (
                    <li key={item} className="flex gap-3">
                      <span className="mt-2 h-1.5 w-1.5 rounded-full bg-primary" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="rounded-3xl border border-white/8 bg-white/5 p-4">
              <p className="text-sm font-semibold text-white">Linked evidence ({evidenceFindings.length})</p>
              <div className="mt-3 space-y-3">
                {selectedIncident.evidence.map((item) => (
                  <div key={item.finding_id} className="rounded-2xl border border-white/8 bg-black/20 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <Badge tone="info">{item.category}</Badge>
                      <span className="text-xs text-muted-foreground">{item.severity}</span>
                    </div>
                    <p className="mt-2 text-sm font-semibold text-white">{item.title}</p>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.summary}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-white/8 bg-white/5 p-4">
            <p className="text-sm font-semibold text-white">Timeline</p>
            <div className="mt-4 space-y-4">
              {buildIncidentTimeline(selectedIncident).map((entry) => (
                <div key={`${entry.label}-${entry.at}`} className="flex gap-4">
                  <div
                    className={`
                      mt-2 h-3 w-3 rounded-full
                      ${
                        entry.tone === "critical"
                          ? "bg-rose-400"
                          : entry.tone === "warning"
                            ? "bg-amber-400"
                            : entry.tone === "success"
                              ? "bg-emerald-400"
                              : "bg-cyan-400"
                      }
                    `}
                  />
                  <div>
                    <p className="text-sm font-medium text-white">{entry.label}</p>
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{formatDateTime(entry.at)}</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">{entry.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
