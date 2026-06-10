export const dynamic = "force-dynamic";

import { DependencyMap } from "@/components/dashboard/dependency-map";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { loadInvestigationBundle } from "@/lib/backend";
import { formatScore } from "@/lib/format";
import { requireCurrentSession } from "@/lib/session";

export default async function GraphPage() {
  const session = await requireCurrentSession("/graph");
  const bundle = await loadInvestigationBundle(session);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Relationship map</p>
              <CardTitle>Impact map</CardTitle>
            </div>
            <Badge tone="info">Average score {formatScore(bundle.stats.averageHealth)}</Badge>
          </div>
          <p className="text-sm leading-6 text-muted-foreground">
            The graph turns health and incidents into a quick view of what is likely affected.
          </p>
        </CardHeader>
      </Card>

      <DependencyMap nodes={bundle.graph.nodes} edges={bundle.graph.edges} />
    </div>
  );
}
