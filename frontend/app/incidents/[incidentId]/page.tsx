export const dynamic = "force-dynamic";

import { notFound } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { FindingsTable } from "@/components/dashboard/findings-table";
import { PostmortemPanel } from "@/components/dashboard/postmortem-panel";
import { loadIncidentBundle } from "@/lib/backend";
import { buildIncidentTimeline, buildPostmortemSummary } from "@/lib/insights";
import { formatConfidence, formatDateTime, formatRelativeTime, titleCase } from "@/lib/format";
import { requireCurrentSession } from "@/lib/session";

interface IncidentDetailPageProps {
  params: Promise<{ incidentId: string }>;
}

export default async function IncidentDetailPage({ params }: IncidentDetailPageProps) {
  const { incidentId } = await params;
  const session = await requireCurrentSession(`/incidents/${incidentId}`);
  const { bundle, incident } = await loadIncidentBundle(incidentId, session);

  if (!incident) {
    notFound();
  }

  const relatedFindings = bundle.findings.filter((finding) => finding.incident_id === incident.id);
  const timeline = buildIncidentTimeline(incident);
  const postmortem = buildPostmortemSummary([incident], relatedFindings);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="gap-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Incident detail</p>
              <CardTitle className="mt-1">{incident.title}</CardTitle>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={incident.state === "resolved" ? "success" : incident.state === "investigating" ? "info" : "warning"}>
                {incident.state}
              </Badge>
              <Badge tone="muted">{incident.scope_kind}</Badge>
              <Button href="/incidents" variant="secondary" size="sm">
                Back to incidents
              </Button>
            </div>
          </div>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{incident.summary}</p>
        </CardHeader>

        <CardBody className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Confidence</p>
            <p className="mt-2 text-2xl font-semibold text-white">{formatConfidence(incident.confidence)}</p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Updated</p>
            <p className="mt-2 text-sm font-semibold text-white">{formatDateTime(incident.updated_at)}</p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Age</p>
            <p className="mt-2 text-sm font-semibold text-white">{formatRelativeTime(incident.created_at)}</p>
          </div>
        </CardBody>
      </Card>

      <section className="grid gap-6 xl:grid-cols-[1fr,0.92fr]">
        <Card>
          <CardHeader className="gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Timeline</p>
            <CardTitle>Evidence chronology</CardTitle>
          </CardHeader>
          <CardBody className="space-y-4">
            {timeline.map((entry) => (
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
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Evidence</p>
            <CardTitle>Linked findings</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3">
            {relatedFindings.map((finding) => (
              <div key={finding.id} className="rounded-2xl border border-white/8 bg-white/5 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Badge tone="info">{finding.category}</Badge>
                  <span className="text-xs text-muted-foreground">{titleCase(finding.severity)}</span>
                </div>
                <p className="mt-2 text-sm font-semibold text-white">{finding.title}</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">{finding.summary}</p>
              </div>
            ))}
          </CardBody>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr,0.9fr]">
        <PostmortemPanel summary={postmortem} updatedAt={bundle.generatedAt} />
        <Card>
          <CardHeader className="gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Actions</p>
            <CardTitle>Response guidance</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3">
            {incident.recommendations.map((recommendation) => (
              <div key={recommendation} className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm leading-6 text-muted-foreground">
                {recommendation}
              </div>
            ))}
          </CardBody>
        </Card>
      </section>

      <FindingsTable findings={relatedFindings} />
    </div>
  );
}
