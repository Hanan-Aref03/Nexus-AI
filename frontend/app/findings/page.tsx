export const dynamic = "force-dynamic";

import { FindingsTable } from "@/components/dashboard/findings-table";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { loadInvestigationBundle } from "@/lib/backend";
import { requireCurrentSession } from "@/lib/session";

export default async function FindingsPage() {
  const session = await requireCurrentSession("/findings");
  const bundle = await loadInvestigationBundle(session);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="gap-3">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Findings</p>
          <CardTitle>Key evidence</CardTitle>
          <p className="text-sm leading-6 text-muted-foreground">
            Search, filter, and inspect the evidence before it becomes a decision.
          </p>
        </CardHeader>
      </Card>

      <FindingsTable findings={bundle.findings} />
    </div>
  );
}
