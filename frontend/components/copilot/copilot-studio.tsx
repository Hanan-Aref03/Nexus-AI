"use client";

import { useMemo, useState } from "react";
import type { CSSProperties } from "react";

import { formatConfidence, formatDateTime } from "@/lib/format";
import { askCopilot } from "@/lib/copilot";
import type { AlertsFeed, CopilotAnswer } from "@/lib/types";
import { cn } from "@/lib/utils";

type SurfaceMode = "night" | "paper";

interface CopilotTurn {
  id: string;
  role: "user" | "assistant";
  text: string;
  provider?: string;
  confidence?: number;
  evidence?: string[];
  followUp?: string;
  evaluation?: CopilotAnswer["evaluation"];
}

interface CopilotStudioProps {
  feed: AlertsFeed;
}

const surfaceTokens: Record<
  SurfaceMode,
  {
    background: string;
    panel: string;
    ink: string;
    muted: string;
    border: string;
    accent: string;
    accentForeground: string;
    glow: string;
  }
> = {
  night: {
    background: "222 47% 9%",
    panel: "222 39% 13%",
    ink: "210 40% 98%",
    muted: "215 18% 72%",
    border: "217 26% 22%",
    accent: "174 79% 53%",
    accentForeground: "222 47% 8%",
    glow: "45 212 191",
  },
  paper: {
    background: "0 0% 100%",
    panel: "210 40% 98%",
    ink: "222 47% 11%",
    muted: "215 16% 45%",
    border: "214 32% 91%",
    accent: "252 70% 50%",
    accentForeground: "0 0% 100%",
    glow: "99 102 241",
  },
};

function makeTurnId(role: CopilotTurn["role"]): string {
  return `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function surfaceFieldClasses(mode: SurfaceMode): string {
  return mode === "night"
    ? "border-[hsl(var(--copilot-border))] bg-[hsl(var(--copilot-panel))] text-[hsl(var(--copilot-ink))] placeholder:text-[hsl(var(--copilot-muted))]"
    : "border-[hsl(var(--copilot-border))] bg-[hsl(var(--copilot-panel))] text-[hsl(var(--copilot-ink))] placeholder:text-[hsl(var(--copilot-muted))]";
}

function themeToggleClasses(active: boolean): string {
  return active
    ? "border-transparent bg-[hsl(var(--copilot-accent))] text-[hsl(var(--copilot-accent-foreground))]"
    : "border-[hsl(var(--copilot-border))] bg-[hsl(var(--copilot-panel))] text-[hsl(var(--copilot-ink))]";
}

export function CopilotStudio({ feed }: CopilotStudioProps) {
  const [mode, setMode] = useState<SurfaceMode>("night");
  const [question, setQuestion] = useState(feed.copilotPrompt);
  const [turns, setTurns] = useState<CopilotTurn[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const topAlert = feed.alerts[0] ?? null;
  const suggestions = useMemo(
    () => [
      feed.copilotPrompt,
      "What evidence supports the top incident?",
      "Is anything security-sensitive here?",
      "What should I inspect next?",
    ],
    [feed.copilotPrompt],
  );

  async function handleAsk(promptText?: string) {
    const nextQuestion = (promptText ?? question).trim();
    if (!nextQuestion || isAsking) {
      return;
    }

    const userTurn: CopilotTurn = {
      id: makeTurnId("user"),
      role: "user",
      text: nextQuestion,
    };
    setTurns((current) => [...current, userTurn]);
    setIsAsking(true);
    setError(null);

    try {
      const answer: CopilotAnswer = await askCopilot(nextQuestion);
      const assistantTurn: CopilotTurn = {
        id: makeTurnId("assistant"),
        role: "assistant",
        text: answer.answer,
        provider: answer.provider,
        confidence: answer.confidence,
        evidence: answer.evidence,
        followUp: answer.followUp,
        evaluation: answer.evaluation,
      };

      setTurns((current) => [...current, assistantTurn]);
      setQuestion(answer.followUp || feed.copilotPrompt);
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Copilot request failed.";
      setError(message);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <section
      className="relative overflow-hidden rounded-[2rem] border p-5 sm:p-6"
      style={
        {
          "--copilot-background": surfaceTokens[mode].background,
          "--copilot-panel": surfaceTokens[mode].panel,
          "--copilot-ink": surfaceTokens[mode].ink,
          "--copilot-muted": surfaceTokens[mode].muted,
          "--copilot-border": surfaceTokens[mode].border,
          "--copilot-accent": surfaceTokens[mode].accent,
          "--copilot-accent-foreground": surfaceTokens[mode].accentForeground,
          "--copilot-glow": surfaceTokens[mode].glow,
        } as CSSProperties
      }
    >
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.18),transparent_30%),radial-gradient(circle_at_top_right,rgba(99,102,241,0.16),transparent_32%),radial-gradient(circle_at_bottom,rgba(255,255,255,0.03),transparent_28%)]" />
      <div className="relative grid gap-6 xl:grid-cols-[1.04fr,0.96fr]">
        <div className="space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[hsl(var(--copilot-muted))]">Copilot studio</p>
              <h2 className="mt-2 text-3xl font-semibold tracking-tight">Ask the workspace what it knows.</h2>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-[hsl(var(--copilot-muted))]">
                The copilot stays grounded in the current tenant's evidence, keeps guardrails on the prompt path, and can switch surfaces between a deep-night control room and a clean paper briefing.
              </p>
            </div>

            <div className="flex items-center gap-2 rounded-full border border-[hsl(var(--copilot-border))] bg-[hsl(var(--copilot-panel))] p-1">
              <button
                type="button"
                onClick={() => setMode("night")}
                className={cn("rounded-full px-3 py-2 text-xs font-semibold transition", themeToggleClasses(mode === "night"))}
              >
                Night
              </button>
              <button
                type="button"
                onClick={() => setMode("paper")}
                className={cn("rounded-full px-3 py-2 text-xs font-semibold transition", themeToggleClasses(mode === "paper"))}
              >
                Paper
              </button>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => setQuestion(suggestion)}
                className="rounded-2xl border border-[hsl(var(--copilot-border))] bg-[hsl(var(--copilot-panel))] px-4 py-3 text-left text-sm leading-6 transition hover:border-[hsl(var(--copilot-accent))]/60"
              >
                {suggestion}
              </button>
            ))}
          </div>

          <div className="rounded-[1.75rem] border border-[hsl(var(--copilot-border))] bg-[hsl(var(--copilot-panel))] p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-[hsl(var(--copilot-muted))]">Current prompt</p>
                <p className="mt-1 text-sm text-[hsl(var(--copilot-muted))]">
                  {feed.copilotPrompt}
                </p>
              </div>
              <div className="rounded-full border border-[hsl(var(--copilot-border))] px-3 py-1 text-xs font-medium text-[hsl(var(--copilot-muted))]">
                {feed.mode === "live" ? "Live workspace" : "Sample workspace"}
              </div>
            </div>

            <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_auto]">
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                rows={4}
                placeholder="Ask about the incident, service health, or what to inspect first..."
                className={cn(
                  "min-h-[120px] w-full rounded-3xl border px-4 py-3 text-sm leading-6 outline-none transition focus:border-[hsl(var(--copilot-accent))]",
                  surfaceFieldClasses(mode),
                )}
              />

              <div className="flex flex-row gap-3 lg:flex-col">
                <button
                  type="button"
                  onClick={() => handleAsk()}
                  disabled={isAsking}
                  className="inline-flex h-12 items-center justify-center rounded-full bg-[hsl(var(--copilot-accent))] px-5 text-sm font-semibold text-[hsl(var(--copilot-accent-foreground))] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isAsking ? "Thinking..." : "Ask"}
                </button>
                <div className="rounded-2xl border border-[hsl(var(--copilot-border))] px-4 py-3 text-xs leading-6 text-[hsl(var(--copilot-muted))]">
                  Gemini first, Grok second, local fallback last.
                </div>
              </div>
            </div>

            {error ? (
              <div className="mt-4 rounded-2xl border border-rose-400/40 bg-rose-500/10 px-4 py-3 text-sm leading-6 text-rose-200">
                {error}
              </div>
            ) : null}
          </div>

          <div className="space-y-3">
            {turns.length === 0 ? (
              <div className="rounded-[1.75rem] border border-dashed border-[hsl(var(--copilot-border))] bg-[hsl(var(--copilot-panel))] p-5 text-sm leading-7 text-[hsl(var(--copilot-muted))]">
                Ask a question to start the transcript. The reply will stay tied to the current evidence and include a small evaluation scorecard.
              </div>
            ) : (
              turns.map((turn) => (
                <article
                  key={turn.id}
                  className={cn(
                    "rounded-[1.75rem] border p-4",
                    turn.role === "user"
                      ? "border-[hsl(var(--copilot-border))] bg-[hsl(var(--copilot-panel))]"
                      : "border-[hsl(var(--copilot-accent))]/20 bg-[hsl(var(--copilot-panel))]",
                  )}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="rounded-full border border-[hsl(var(--copilot-border))] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[hsl(var(--copilot-muted))]">
                        {turn.role === "user" ? "You" : "Copilot"}
                      </span>
                      {turn.provider ? (
                        <span className="rounded-full border border-[hsl(var(--copilot-border))] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[hsl(var(--copilot-muted))]">
                          {turn.provider}
                        </span>
                      ) : null}
                    </div>
                    {turn.confidence !== undefined ? (
                      <span className="text-xs text-[hsl(var(--copilot-muted))]">{formatConfidence(turn.confidence)}</span>
                    ) : null}
                  </div>

                  <p className="mt-3 text-sm leading-7 text-[hsl(var(--copilot-ink))]">{turn.text}</p>

                  {turn.evidence && turn.evidence.length > 0 ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {turn.evidence.map((item) => (
                        <span
                          key={item}
                          className="rounded-full border border-[hsl(var(--copilot-border))] px-3 py-1 text-[11px] text-[hsl(var(--copilot-muted))]"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  ) : null}

                  {turn.evaluation ? (
                    <div className="mt-4 grid gap-2 sm:grid-cols-3">
                      <MetricPill label="Faithfulness" value={turn.evaluation.faithfulness} mode={mode} />
                      <MetricPill label="Relevancy" value={turn.evaluation.answerRelevancy} mode={mode} />
                      <MetricPill label="Context" value={turn.evaluation.contextPrecision} mode={mode} />
                    </div>
                  ) : null}

                  {turn.followUp ? (
                    <p className="mt-4 text-xs uppercase tracking-[0.2em] text-[hsl(var(--copilot-muted))]">
                      Next: {turn.followUp}
                    </p>
                  ) : null}
                </article>
              ))
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-[1.75rem] border border-[hsl(var(--copilot-border))] bg-[hsl(var(--copilot-panel))] p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[hsl(var(--copilot-muted))]">Simulation</p>
                <h3 className="mt-2 text-xl font-semibold">Antigravity signal room</h3>
              </div>
              <span className="rounded-full border border-[hsl(var(--copilot-border))] px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-[hsl(var(--copilot-muted))]">
                {feed.summary.total} alerts
              </span>
            </div>

            <div className="relative mt-5 flex h-56 items-center justify-center overflow-hidden rounded-[1.75rem] border border-[hsl(var(--copilot-border))] bg-[radial-gradient(circle_at_center,rgb(var(--copilot-glow)_/_0.14),transparent_26%),linear-gradient(180deg,rgba(255,255,255,0.02),transparent)]">
              <div className="absolute inset-0 rounded-[1.75rem] bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.08),transparent_22%),radial-gradient(circle_at_bottom_right,rgba(255,255,255,0.05),transparent_30%)]" />
              <div className="absolute h-24 w-24 rounded-full border border-[hsl(var(--copilot-accent))]/40 animate-pulse" />
              <div className="absolute h-40 w-40 rounded-full border border-[hsl(var(--copilot-accent))]/18" />
              <div className="absolute h-56 w-56 rounded-full border border-dashed border-[hsl(var(--copilot-border))]/70" />
              <div className="absolute left-12 top-12 h-4 w-4 rounded-full bg-[hsl(var(--copilot-accent))] shadow-[0_0_24px_rgb(var(--copilot-glow)_/_0.45)]" />
              <div className="absolute right-16 top-20 h-3.5 w-3.5 rounded-full bg-cyan-300/80 animate-bounce" />
              <div className="absolute bottom-14 left-20 h-3 w-3 rounded-full bg-violet-300/80 animate-pulse" />
              <div className="absolute bottom-12 right-12 h-5 w-5 rounded-full bg-white/90 shadow-[0_0_26px_rgba(255,255,255,0.28)]" />
              <div className="relative flex h-24 w-24 items-center justify-center rounded-full border border-[hsl(var(--copilot-accent))]/40 bg-[hsl(var(--copilot-background))]/80">
                <div className="text-center">
                  <p className="text-[10px] uppercase tracking-[0.2em] text-[hsl(var(--copilot-muted))]">Response</p>
                  <p className="mt-1 text-lg font-semibold">{Math.round((topAlert?.confidence ?? 0.5) * 100)}%</p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <StatCard label="Latest signal" value={topAlert?.title ?? "No active alert"} note={topAlert?.summary ?? feed.sourceReason} mode={mode} />
            <StatCard
              label="Security share"
              value={`${feed.summary.security}/${feed.summary.total || 1}`}
              note={feed.summary.security > 0 ? "Security evidence is already in the same flow." : "No security-specific alert is active yet."}
              mode={mode}
            />
            <StatCard
              label="Workspace posture"
              value={feed.mode === "live" ? "Live" : "Sample"}
              note={formatDateTime(feed.generatedAt)}
              mode={mode}
            />
          </div>

          <div className="rounded-[1.75rem] border border-[hsl(var(--copilot-border))] bg-[hsl(var(--copilot-panel))] p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[hsl(var(--copilot-muted))]">Workspace source</p>
            <p className="mt-2 text-sm leading-7 text-[hsl(var(--copilot-ink))]">{feed.sourceReason}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="rounded-full border border-[hsl(var(--copilot-border))] px-3 py-1 text-xs text-[hsl(var(--copilot-muted))]">
                {feed.sourceLabel}
              </span>
              <span className="rounded-full border border-[hsl(var(--copilot-border))] px-3 py-1 text-xs text-[hsl(var(--copilot-muted))]">
                Generated {formatDateTime(feed.generatedAt)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

interface MetricPillProps {
  label: string;
  value: number;
  mode: SurfaceMode;
}

function MetricPill({ label, value, mode }: MetricPillProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border px-3 py-2 text-sm",
        mode === "night"
          ? "border-white/8 bg-white/5"
          : "border-[hsl(var(--copilot-border))] bg-white/80",
      )}
    >
      <p className="text-[11px] uppercase tracking-[0.18em] text-[hsl(var(--copilot-muted))]">{label}</p>
      <p className="mt-1 font-semibold">{Math.round(value * 100)}%</p>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  note: string;
  mode: SurfaceMode;
}

function StatCard({ label, value, note, mode }: StatCardProps) {
  return (
    <div
      className={cn(
        "rounded-[1.5rem] border p-4",
        mode === "night"
          ? "border-white/8 bg-white/5"
          : "border-[hsl(var(--copilot-border))] bg-white/80",
      )}
    >
      <p className="text-[11px] uppercase tracking-[0.18em] text-[hsl(var(--copilot-muted))]">{label}</p>
      <p className="mt-2 text-lg font-semibold">{value}</p>
      <p className="mt-2 text-xs leading-6 text-[hsl(var(--copilot-muted))]">{note}</p>
    </div>
  );
}
