export const dynamic = "force-dynamic";

import { AlertsBoard } from "@/components/alerts/alerts-board";
import { CopilotStudio } from "@/components/copilot/copilot-studio";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, MetricCard } from "@/components/ui/card";
import { formatDateTime } from "@/lib/format";
import { loadAlertsFeed } from "@/lib/backend";
import { requireCurrentSession } from "@/lib/session";

export default async function AlertsPage() {
  const session = await requireCurrentSession("/alerts");
  const feed = await loadAlertsFeed(session);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Alerts and copilot</p>
              <CardTitle>One queue for urgent work</CardTitle>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge tone={feed.mode === "live" ? "success" : "warning"}>{feed.mode === "live" ? "Live feed" : "Sample feed"}</Badge>
              <Badge tone="info">Generated {formatDateTime(feed.generatedAt)}</Badge>
            </div>
          </div>
          <p className="text-sm leading-6 text-muted-foreground">Keep the feed focused on incidents, health, and the next question to ask.</p>
        </CardHeader>
      </Card>

      <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Active alerts"
          value={String(feed.summary.total)}
          detail={`Derived from ${feed.summary.incidents} incident(s) and ${feed.summary.health} health signal(s).`}
          accent="bg-gradient-to-r from-rose-500 via-orange-400 to-amber-300"
          trend="In the queue"
          sparkline={[18, 24, 30, 38, 42, 50, 58, 64]}
        />
        <MetricCard
          label="Critical items"
          value={String(feed.summary.critical)}
          detail="The most urgent signals are already consolidated into the inbox."
          accent="bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-300"
          trend="Immediate attention"
          sparkline={[10, 14, 18, 22, 26, 30, 36, 40]}
        />
        <MetricCard
          label="Security alerts"
          value={String(feed.summary.security)}
          detail="Security-specific alerts stay in the same path as operational response."
          accent="bg-gradient-to-r from-amber-400 via-orange-400 to-rose-400"
          trend="Tenant aware"
          sparkline={[8, 12, 16, 20, 18, 24, 28, 32]}
        />
        <MetricCard
          label="Active scopes"
          value={String(feed.summary.scopes)}
          detail={`The feed covers ${feed.summary.scopes} unique service or workload scope(s).`}
          accent="bg-gradient-to-r from-violet-400 via-cyan-300 to-primary"
          trend="Cross-surface"
          sparkline={[32, 36, 42, 46, 50, 54, 58, 62]}
        />
      </section>

      <CopilotStudio feed={feed} />

      <AlertsBoard feed={feed} />
    </div>
  );
}
