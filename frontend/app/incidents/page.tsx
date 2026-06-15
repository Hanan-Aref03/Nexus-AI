export const dynamic = "force-dynamic";

import { IncidentExplorer } from "@/components/dashboard/incident-explorer";
import { DependencyMap } from "@/components/dashboard/dependency-map";
import { PostmortemPanel } from "@/components/dashboard/postmortem-panel";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { loadInvestigationBundle } from "@/lib/backend";
import { requireCurrentSession } from "@/lib/session";

export default async function IncidentsPage() {
  const session = await requireCurrentSession("/incidents");
  const bundle = await loadInvestigationBundle(session);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="gap-3">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Incidents</p>
          <CardTitle>Active incident room</CardTitle>
          <p className="text-sm leading-6 text-muted-foreground">
            Focus on evidence, impact, and the most likely cause behind each open thread.
          </p>
        </CardHeader>
      </Card>

      <IncidentExplorer incidents={bundle.incidents} findings={bundle.findings} />

      <section className="grid gap-6 xl:grid-cols-[1fr,0.95fr]">
        <DependencyMap nodes={bundle.graph.nodes} edges={bundle.graph.edges} compact />
        <PostmortemPanel summary={bundle.postmortem} updatedAt={bundle.generatedAt} />
      </section>
    </div>
  );
}
