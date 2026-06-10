export const dynamic = "force-dynamic";

import { DashboardHero } from "@/components/dashboard/hero";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { DependencyMap } from "@/components/dashboard/dependency-map";
import { FindingsTable } from "@/components/dashboard/findings-table";
import { IncidentExplorer } from "@/components/dashboard/incident-explorer";
import { PostmortemPanel } from "@/components/dashboard/postmortem-panel";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { loadInvestigationBundle } from "@/lib/backend";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/format";
import { requireCurrentSession } from "@/lib/session";
import { getRoleProfile } from "@/lib/auth";

export default async function HomePage() {
  const session = await requireCurrentSession("/");
  const bundle = await loadInvestigationBundle(session);

  return (
    <div className="space-y-6">
      <DashboardHero
        mode={bundle.mode}
        sourceLabel={bundle.sourceLabel}
        sourceReason={bundle.sourceReason}
        generatedAt={bundle.generatedAt}
        systemStatus={bundle.backendHealth?.status ?? "unavailable"}
        storageStatus={bundle.backendReady?.database.status ?? "unknown"}
        workspaceName={session.tenantName}
        roleLabel={getRoleProfile(session.role).label}
      />

      <KpiGrid stats={bundle.stats} />

      <section className="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
        <IncidentExplorer incidents={bundle.incidents} findings={bundle.findings} />
        <div className="space-y-6">
          <DependencyMap nodes={bundle.graph.nodes} edges={bundle.graph.edges} compact />
          <PostmortemPanel summary={bundle.postmortem} updatedAt={bundle.generatedAt} />
        </div>
      </section>

      <FindingsTable findings={bundle.findings} />

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Data state</p>
              <CardTitle className="mt-1">Workspace snapshot</CardTitle>
            </div>
            <Badge tone={bundle.mode === "live" ? "success" : "warning"}>{bundle.mode === "live" ? "Live" : "Sample"}</Badge>
          </div>
          <p className="text-sm leading-6 text-muted-foreground">
            When live data is available it is used first. If not, the workspace stays useful with a curated sample scenario.
          </p>
        </CardHeader>
        <CardBody className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Generated</p>
            <p className="mt-2 text-sm font-semibold text-white">{formatDateTime(bundle.generatedAt)}</p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Findings</p>
            <p className="mt-2 text-sm font-semibold text-white">{bundle.findings.length}</p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Incidents</p>
            <p className="mt-2 text-sm font-semibold text-white">{bundle.incidents.length}</p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
