import { MetricCard } from "@/components/ui/card";
import type { DashboardStats } from "@/lib/types";
import { formatScore } from "@/lib/format";

interface KpiGridProps {
  stats: DashboardStats;
}

export function KpiGrid({ stats }: KpiGridProps) {
  return (
    <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
      <MetricCard
        label="Open incidents"
        value={String(stats.openIncidents)}
        detail={`Most active work is centered on ${stats.topService}.`}
        accent="bg-gradient-to-r from-rose-500 via-orange-400 to-amber-300"
        trend="Focus now"
        sparkline={[18, 24, 30, 38, 46, 54, 62, 58]}
      />
      <MetricCard
        label="Critical findings"
        value={String(stats.criticalFindings)}
        detail="The most urgent evidence is already grouped for review."
        accent="bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-300"
        trend="Evidence-backed"
        sparkline={[10, 16, 22, 30, 28, 40, 36, 44]}
      />
      <MetricCard
        label="Watch services"
        value={String(stats.watchServices)}
        detail="These services need attention before they escalate."
        accent="bg-gradient-to-r from-amber-400 via-orange-400 to-rose-400"
        trend="Pre-incident"
        sparkline={[14, 20, 18, 24, 28, 26, 30, 34]}
      />
      <MetricCard
        label="Average health"
        value={formatScore(stats.averageHealth)}
        detail={`Lowest-scored scope: ${stats.topService}. Latest signal: ${stats.latestSignal}.`}
        accent="bg-gradient-to-r from-violet-400 via-cyan-300 to-primary"
        trend="Fleet wide"
        sparkline={[64, 70, 74, 76, 80, 82, 84, 86]}
      />
    </section>
  );
}
