"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { formatScore } from "@/lib/format";
import type { GraphEdge, GraphNode } from "@/lib/types";

interface DependencyMapProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  compact?: boolean;
}

export function DependencyMap({ nodes, edges, compact = false }: DependencyMapProps) {
  const [selectedNodeId, setSelectedNodeId] = useState(nodes[0]?.id ?? "");
  const selectedNode = nodes.find((node) => node.id === selectedNodeId) ?? nodes[0];

  return (
    <Card className="overflow-hidden">
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Impact map</p>
            <CardTitle className="mt-1">Relationship view</CardTitle>
          </div>
          <Badge tone="muted">{nodes.length} nodes</Badge>
        </div>
        <p className="text-sm leading-6 text-muted-foreground">
          A clear view of relationships so affected areas stay easy to spot during review.
        </p>
      </CardHeader>

      <CardBody className={compact ? "space-y-4" : "grid gap-5 xl:grid-cols-[1.2fr,0.8fr]"}>
        <div className="relative min-h-[420px] overflow-hidden rounded-3xl border border-white/8 bg-black/20 p-4">
          <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            {edges.map((edge) => {
              const source = nodes.find((node) => node.id === edge.source);
              const target = nodes.find((node) => node.id === edge.target);
              if (!source || !target) {
                return null;
              }

              return (
                <line
                  key={edge.id}
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke="rgba(255,255,255,0.16)"
                  strokeDasharray={edge.weight > 2 ? "0" : "2 2"}
                  strokeWidth={edge.weight > 2 ? 0.6 : 0.35}
                />
              );
            })}
          </svg>

          {nodes.map((node) => {
            const active = node.id === selectedNodeId;
            return (
              <button
                key={node.id}
                onClick={() => setSelectedNodeId(node.id)}
                className={`
                  absolute -translate-x-1/2 -translate-y-1/2 rounded-full border px-4 py-3 text-left transition-all duration-200
                  ${active ? "scale-105 border-primary/40 bg-primary/15 shadow-[0_0_28px_rgba(45,212,191,0.2)]" : "border-white/8 bg-white/5 hover:bg-white/8"}
                `}
                style={{
                  left: `${node.x}%`,
                  top: `${node.y}%`,
                  minWidth: compact ? "110px" : "150px",
                }}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">{node.kind}</span>
                  <span className={`h-2.5 w-2.5 rounded-full ${node.status === "critical" ? "bg-rose-400" : node.status === "degraded" ? "bg-orange-400" : node.status === "watch" ? "bg-amber-400" : "bg-emerald-400"}`} />
                </div>
                <div className="mt-2 text-sm font-semibold text-white">{node.label}</div>
                <div className="mt-1 text-xs text-muted-foreground">{formatScore(node.score)} score</div>
              </button>
            );
          })}
        </div>

        {compact ? null : selectedNode ? (
          <div className="rounded-3xl border border-white/8 bg-white/5 p-5">
            <Badge
              tone={
                selectedNode.status === "critical"
                  ? "danger"
                  : selectedNode.status === "degraded"
                    ? "warning"
                    : selectedNode.status === "watch"
                      ? "warning"
                      : "success"
              }
            >
              {selectedNode.status}
            </Badge>
            <h3 className="mt-4 text-xl font-semibold text-white">{selectedNode.label}</h3>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{selectedNode.description}</p>

            <div className="mt-5 grid gap-3">
              <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Health score</p>
                <p className="mt-2 text-3xl font-semibold text-white">{selectedNode.score}</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Incidents</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{selectedNode.incident_count}</p>
                </div>
                <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Findings</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{selectedNode.finding_count}</p>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </CardBody>
    </Card>
  );
}
