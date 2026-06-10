"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDateTime } from "@/lib/format";
import type { PostmortemSummary } from "@/lib/types";

interface PostmortemPanelProps {
  summary: PostmortemSummary;
  updatedAt: string;
}

export function PostmortemPanel({ summary, updatedAt }: PostmortemPanelProps) {
  const [copied, setCopied] = useState(false);

  async function copySummary() {
    const text = [
      `Headline: ${summary.headline}`,
      `Summary: ${summary.summary}`,
      ...summary.sections.map((section) => `${section.title}: ${section.body}`),
      `Actions: ${summary.action_items.join(" | ")}`,
    ].join("\n");

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <Card>
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Summary draft</p>
            <CardTitle className="mt-1">{summary.headline}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone="info">Updated {formatDateTime(updatedAt)}</Badge>
            <Button size="sm" variant="secondary" onClick={copySummary}>
              {copied ? "Copied" : "Copy summary"}
            </Button>
          </div>
        </div>
        <p className="text-sm leading-6 text-muted-foreground">{summary.summary}</p>
      </CardHeader>
      <CardBody className="space-y-5">
        {summary.sections.map((section) => (
          <div key={section.title} className="rounded-2xl border border-white/8 bg-white/5 p-4">
            <p className="text-sm font-semibold text-white">{section.title}</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{section.body}</p>
          </div>
        ))}

        <div className="rounded-2xl border border-primary/20 bg-primary/10 p-4">
          <p className="text-sm font-semibold text-white">Next steps</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
            {summary.action_items.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-2 h-1.5 w-1.5 rounded-full bg-primary" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </CardBody>
    </Card>
  );
}
