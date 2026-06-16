import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { formatDateTime } from "@/lib/format";

interface HeroProps {
  mode: "live" | "demo";
  sourceLabel: string;
  sourceReason: string;
  generatedAt: string;
  systemStatus: string;
  storageStatus: string;
  workspaceName: string;
  roleLabel: string;
}

export function DashboardHero({
  mode,
  sourceLabel,
  sourceReason,
  generatedAt,
  systemStatus,
  storageStatus,
  workspaceName,
  roleLabel,
}: HeroProps) {
  const systemLabel = systemStatus === "ok" ? "Healthy" : systemStatus === "unavailable" ? "Unavailable" : systemStatus;
  const storageLabel = storageStatus === "ready" ? "Ready" : storageStatus === "degraded" ? "Degraded" : storageStatus;
  const systemTone = systemStatus === "ok" ? "success" : "warning";
  const storageTone = storageStatus === "ready" ? "success" : "warning";

  return (
    <Card className="overflow-hidden border-white/10">
      <CardHeader className="gap-4 p-6 sm:p-8">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone={mode === "live" ? "success" : "warning"}>{sourceLabel}</Badge>
          <Badge tone="info">{workspaceName}</Badge>
          <Badge tone="muted">{roleLabel}</Badge>
          <Badge tone={systemTone}>System {systemLabel}</Badge>
          <Badge tone={storageTone}>Storage {storageLabel}</Badge>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.6fr,1fr]">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-muted-foreground">Workspace overview</p>
            <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
              See what changed and what needs attention.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-muted-foreground">{sourceReason}</p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Button href="/incidents">Incidents</Button>
              <Button href="/findings" variant="secondary">
                Findings
              </Button>
              <Button href="/postmortems" variant="outline">
                Summary
              </Button>
            </div>
          </div>

          <Card className="bg-black/20">
            <CardBody className="p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Status snapshot</p>
              <div className="mt-4 space-y-4">
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Generated</p>
                  <p className="mt-2 text-lg font-semibold text-white">{formatDateTime(generatedAt)}</p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-white/8 bg-white/5 p-3">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Mode</p>
                    <p className="mt-2 text-sm font-semibold text-white">{mode === "live" ? "Live" : "Sample"}</p>
                  </div>
                  <div className="rounded-2xl border border-white/8 bg-white/5 p-3">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Workspace</p>
                    <p className="mt-2 text-sm font-semibold text-white">{workspaceName}</p>
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </CardHeader>
    </Card>
  );
}
