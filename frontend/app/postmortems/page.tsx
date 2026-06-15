export const dynamic = "force-dynamic";

import { PostmortemPanel } from "@/components/dashboard/postmortem-panel";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { loadInvestigationBundle } from "@/lib/backend";
import { formatDateTime } from "@/lib/format";
import { requireCurrentSession } from "@/lib/session";

export default async function PostmortemsPage() {
  const session = await requireCurrentSession("/postmortems");
  const bundle = await loadInvestigationBundle(session);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Postmortems</p>
              <CardTitle>Summary draft</CardTitle>
            </div>
            <Badge tone="success">Generated {formatDateTime(bundle.generatedAt)}</Badge>
          </div>
          <p className="text-sm leading-6 text-muted-foreground">
            Turn the incident summary into a clear draft that can move straight into review.
          </p>
        </CardHeader>
      </Card>

      <PostmortemPanel summary={bundle.postmortem} updatedAt={bundle.generatedAt} />
    </div>
  );
}
