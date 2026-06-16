"use client";

import { useMemo, useState } from "react";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle, MetricCard } from "@/components/ui/card";
import { formatConfidence, formatDateTime, formatScore, titleCase } from "@/lib/format";
import type { FinOpsInsights } from "@/lib/types";
import { cn } from "@/lib/utils";

type FocusMode = "savings" | "reliability";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

interface FinOpsBoardProps {
  insights: FinOpsInsights;
}

function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

export function FinOpsBoard({ insights }: FinOpsBoardProps) {
  const [focus, setFocus] = useState<FocusMode>("savings");

  const bestOpportunity = insights.opportunities[0] ?? null;
  const bestForecast = insights.forecasts[0] ?? null;
  const focusHeadline = focus === "savings" ? bestOpportunity?.headline : bestForecast?.headline;
  const focusSummary = focus === "savings" ? bestOpportunity?.summary : bestForecast?.summary;
  const focusEvidence = focus === "savings" ? bestOpportunity?.evidence ?? [] : bestForecast?.evidence ?? [];
  const focusRecommendations = focus === "savings" ? bestOpportunity?.recommendations ?? [] : bestForecast?.recommendations ?? [];
  const riskBars = useMemo(
    () => [
      Math.max(18, Math.min(72, insights.estimatedMonthlySavings / 6)),
      Math.max(20, Math.min(76, insights.riskScore)),
      Math.max(22, Math.min(68, insights.opportunityCount * 12 + 20)),
      Math.max(18, Math.min(70, insights.forecastCount * 14 + 18)),
    ],
    [insights.estimatedMonthlySavings, insights.forecastCount, insights.opportunityCount, insights.riskScore],
  );

  return (
    <section className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top_left,rgba(251,191,36,0.12),transparent_22%),radial-gradient(circle_at_top_right,rgba(34,211,238,0.12),transparent_24%),linear-gradient(180deg,rgba(255,255,255,0.03),transparent)] p-5 sm:p-6">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.03),transparent_22%)]" />

      <div className="relative flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">Phase 5 - FinOps and predictive reliability</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Spend less, fail later, and keep the evidence visible.</h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground">
            The final workspace slice turns current findings and health scores into savings opportunities and conservative forecasts. No paid billing feed is required for this first cut.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={insights.mode === "live" ? "success" : "warning"}>{insights.mode === "live" ? "Live analysis" : "Sample scenario"}</Badge>
          <Badge tone="info">Generated {formatDateTime(insights.generatedAt)}</Badge>
          <Button href="/alerts" variant="outline" size="sm">
            Open alerts
          </Button>
        </div>
      </div>

      <section className="mt-6 grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Estimated savings"
          value={formatCurrency(insights.estimatedMonthlySavings)}
          detail="Conservative monthly savings identified from current evidence."
          accent="bg-gradient-to-r from-amber-400 via-orange-400 to-rose-400"
          trend="Right-sizing first"
          sparkline={[18, 26, 28, 32, 42, 46, 54, 62]}
        />
        <MetricCard
          label="Risk score"
          value={formatScore(insights.riskScore)}
          detail="Higher scores mean more capacity or reliability pressure to review."
          accent="bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-300"
          trend="Conservative"
          sparkline={[20, 24, 28, 30, 36, 42, 48, 54]}
        />
        <MetricCard
          label="Opportunities"
          value={String(insights.opportunityCount)}
          detail="Each opportunity is grounded in the current analysis store."
          accent="bg-gradient-to-r from-violet-400 via-indigo-400 to-cyan-300"
          trend="Actionable"
          sparkline={[10, 12, 16, 20, 24, 28, 30, 34]}
        />
        <MetricCard
          label="Forecasts"
          value={String(insights.forecastCount)}
          detail="Predictive signals are kept conservative and explainable."
          accent="bg-gradient-to-r from-sky-400 via-cyan-300 to-emerald-200"
          trend="Watchlist"
          sparkline={[8, 10, 14, 18, 22, 26, 30, 36]}
        />
      </section>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.05fr,0.95fr]">
        <div className="space-y-6">
          <Card>
            <CardHeader className="gap-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Opportunity lane</p>
                  <CardTitle className="mt-1">Where the workspace is leaking spend</CardTitle>
                  <CardDescription className="mt-1 max-w-2xl">
                    The first phase-5 cut prefers conservative estimates and easy-to-explain fixes over flashy billing guesses.
                  </CardDescription>
                </div>
                <Badge tone="muted">{insights.topScope ?? "workspace"}</Badge>
              </div>
            </CardHeader>
            <CardBody className="space-y-3">
              {insights.opportunities.length > 0 ? (
                insights.opportunities.map((opportunity) => (
                  <article
                    key={`${opportunity.kind}-${opportunity.scopeName}`}
                    className="rounded-[1.5rem] border border-white/8 bg-white/5 p-4 transition hover:border-cyan-500/30"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge tone="info">{titleCase(opportunity.kind)}</Badge>
                          <Badge tone="muted">{titleCase(opportunity.scopeKind)}</Badge>
                        </div>
                        <h3 className="text-base font-semibold text-white">{opportunity.headline}</h3>
                        <p className="max-w-3xl text-sm leading-7 text-muted-foreground">{opportunity.summary}</p>
                      </div>

                      <div className="min-w-[160px] rounded-2xl border border-white/8 bg-black/20 px-4 py-3 text-right">
                        <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Monthly savings</p>
                        <p className="mt-1 text-lg font-semibold text-white">{formatCurrency(opportunity.estimatedMonthlySavings)}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{formatConfidence(opportunity.confidence)}</p>
                      </div>
                    </div>

                    {opportunity.evidence.length > 0 ? (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {opportunity.evidence.map((item) => (
                          <span key={item} className="rounded-full border border-white/8 bg-black/20 px-3 py-1 text-[11px] text-muted-foreground">
                            {item}
                          </span>
                        ))}
                      </div>
                    ) : null}

                    <div className="mt-4 grid gap-2 sm:grid-cols-2">
                      {opportunity.recommendations.map((item) => (
                        <div key={item} className="rounded-2xl border border-white/8 bg-black/20 px-3 py-2 text-sm leading-6 text-foreground">
                          {item}
                        </div>
                      ))}
                    </div>
                  </article>
                ))
              ) : (
                <div className="rounded-[1.5rem] border border-dashed border-white/10 bg-white/5 p-5 text-sm leading-7 text-muted-foreground">
                  No savings opportunities are active yet. The workspace is still useful, but there is nothing expensive enough to tune right now.
                </div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader className="gap-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Recommended next moves</p>
                  <CardTitle className="mt-1">Keep the fix list short and the payoff obvious</CardTitle>
                </div>
                <Badge tone={insights.mode === "live" ? "success" : "warning"}>{insights.sourceLabel}</Badge>
              </div>
              <CardDescription>{insights.sourceReason}</CardDescription>
            </CardHeader>
            <CardBody className="grid gap-3 sm:grid-cols-2">
              {insights.recommendations.length > 0 ? (
                insights.recommendations.map((item) => (
                  <div key={item} className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm leading-6 text-foreground">
                    {item}
                  </div>
                ))
              ) : (
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm leading-6 text-muted-foreground">
                  No action items yet. The final workspace slice is calm, which is exactly what we want before the next phase.
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader className="gap-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Forecast lane</p>
                  <CardTitle className="mt-1">What might need attention next</CardTitle>
                  <CardDescription className="mt-1 max-w-2xl">
                    The right-hand lens can switch between savings and reliability to keep the phase easy to inspect.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 p-1">
                  <button
                    type="button"
                    onClick={() => setFocus("savings")}
                    className={cn(
                      "rounded-full px-3 py-2 text-xs font-semibold transition",
                      focus === "savings" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-white",
                    )}
                  >
                    Savings lens
                  </button>
                  <button
                    type="button"
                    onClick={() => setFocus("reliability")}
                    className={cn(
                      "rounded-full px-3 py-2 text-xs font-semibold transition",
                      focus === "reliability" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-white",
                    )}
                  >
                    Reliability lens
                  </button>
                </div>
              </div>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="relative overflow-hidden rounded-[1.75rem] border border-white/8 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.16),transparent_26%),radial-gradient(circle_at_bottom,rgba(251,191,36,0.12),transparent_24%),linear-gradient(180deg,rgba(255,255,255,0.03),transparent)] p-5">
                <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.04),transparent_24%)]" />
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Current focus</p>
                    <p className="mt-1 text-lg font-semibold text-white">{focus === "savings" ? "Savings" : "Reliability"}</p>
                  </div>
                  <Badge tone={focus === "savings" ? "info" : "warning"}>{focus === "savings" ? "Cost first" : "Risk first"}</Badge>
                </div>

                <div className="mt-5 flex h-56 items-center justify-center overflow-hidden rounded-[1.5rem] border border-white/8 bg-black/20">
                  <div className="relative flex h-28 w-28 items-center justify-center rounded-full border border-cyan-400/30 bg-black/40">
                    <div className="text-center">
                      <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{focus === "savings" ? "Savings" : "Risk"}</p>
                      <p className="mt-1 text-2xl font-semibold text-white">
                        {focus === "savings" ? formatCurrency(insights.estimatedMonthlySavings) : formatScore(insights.riskScore)}
                      </p>
                    </div>
                  </div>
                  <div className="absolute h-40 w-40 rounded-full border border-cyan-400/20" />
                  <div className="absolute h-56 w-56 rounded-full border border-dashed border-white/10" />
                  <div className="absolute left-12 top-12 h-3.5 w-3.5 rounded-full bg-cyan-300 shadow-[0_0_24px_rgba(103,232,249,0.45)]" />
                  <div className="absolute right-14 top-20 h-3 w-3 rounded-full bg-amber-300 animate-pulse" />
                  <div className="absolute bottom-14 left-16 h-4 w-4 rounded-full bg-violet-300/90 animate-bounce" />
                  <div className="absolute bottom-12 right-12 h-5 w-5 rounded-full bg-white/90 shadow-[0_0_18px_rgba(255,255,255,0.35)]" />
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl border border-white/8 bg-black/20 p-3">
                    <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Top scope</p>
                    <p className="mt-1 text-sm font-semibold text-white">{insights.topScope ?? "workspace"}</p>
                  </div>
                  <div className="rounded-2xl border border-white/8 bg-black/20 p-3">
                    <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Horizon</p>
                    <p className="mt-1 text-sm font-semibold text-white">{focus === "savings" ? `${bestOpportunity?.horizonDays ?? 42} days` : `${bestForecast?.horizonDays ?? 42} days`}</p>
                  </div>
                  <div className="rounded-2xl border border-white/8 bg-black/20 p-3">
                    <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Confidence</p>
                    <p className="mt-1 text-sm font-semibold text-white">{focus === "savings" ? formatConfidence(bestOpportunity?.confidence ?? 0.66) : formatConfidence(bestForecast?.confidence ?? 0.66)}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-[1.5rem] border border-white/8 bg-white/5 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Focus details</p>
                <h3 className="mt-2 text-lg font-semibold text-white">{focusHeadline ?? "No active focus yet"}</h3>
                <p className="mt-3 text-sm leading-7 text-muted-foreground">{focusSummary ?? "The current workspace is calm, so the focus lens stays conservative."}</p>

                {focusEvidence.length > 0 ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {focusEvidence.map((item) => (
                      <span key={item} className="rounded-full border border-white/8 bg-black/20 px-3 py-1 text-[11px] text-muted-foreground">
                        {item}
                      </span>
                    ))}
                  </div>
                ) : null}

                {focusRecommendations.length > 0 ? (
                  <div className="mt-4 space-y-2">
                    {focusRecommendations.map((item) => (
                      <div key={item} className="rounded-2xl border border-white/8 bg-black/20 px-3 py-2 text-sm leading-6 text-foreground">
                        {item}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader className="gap-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Forecast cards</p>
                  <CardTitle className="mt-1">What will probably need a follow-up</CardTitle>
                </div>
                <Badge tone="muted">{insights.forecasts.length} forecast(s)</Badge>
              </div>
            </CardHeader>
            <CardBody className="space-y-3">
              {insights.forecasts.length > 0 ? (
                insights.forecasts.map((forecast) => (
                  <article key={`${forecast.kind}-${forecast.scopeName ?? "workspace"}`} className="rounded-[1.5rem] border border-white/8 bg-white/5 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge tone={forecast.riskLevel === "high" ? "danger" : forecast.riskLevel === "elevated" ? "warning" : "muted"}>
                            {titleCase(forecast.kind)}
                          </Badge>
                          {forecast.scopeKind ? <Badge tone="info">{titleCase(forecast.scopeKind)}</Badge> : null}
                        </div>
                        <h3 className="text-base font-semibold text-white">{forecast.headline}</h3>
                        <p className="max-w-3xl text-sm leading-7 text-muted-foreground">{forecast.summary}</p>
                      </div>
                      <div className="min-w-[140px] rounded-2xl border border-white/8 bg-black/20 px-4 py-3 text-right">
                        <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Horizon</p>
                        <p className="mt-1 text-lg font-semibold text-white">{forecast.horizonDays}d</p>
                        <p className="mt-1 text-xs text-muted-foreground">{formatConfidence(forecast.confidence)}</p>
                      </div>
                    </div>

                    {forecast.evidence.length > 0 ? (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {forecast.evidence.map((item) => (
                          <span key={item} className="rounded-full border border-white/8 bg-black/20 px-3 py-1 text-[11px] text-muted-foreground">
                            {item}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </article>
                ))
              ) : (
                <div className="rounded-[1.5rem] border border-dashed border-white/10 bg-white/5 p-5 text-sm leading-7 text-muted-foreground">
                  Forecasts will appear once the workspace gathers enough evidence to make a conservative prediction.
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-[1.5rem] border border-white/8 bg-black/20 px-4 py-3 text-sm leading-6 text-muted-foreground">
        <span>Predictive reliability stays on a free, local-friendly path until a real billing feed is worth the extra complexity.</span>
        <Link href="/postmortems" className="font-semibold text-white underline-offset-4 hover:underline">
          Review postmortem guidance
        </Link>
      </div>
    </section>
  );
}
