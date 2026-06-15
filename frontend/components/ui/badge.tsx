import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type BadgeTone = "default" | "success" | "warning" | "danger" | "info" | "muted";

const toneClasses: Record<BadgeTone, string> = {
  default: "border-border bg-white/5 text-foreground",
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-100",
  warning: "border-amber-500/30 bg-amber-500/10 text-amber-100",
  danger: "border-rose-500/30 bg-rose-500/10 text-rose-100",
  info: "border-cyan-500/30 bg-cyan-500/10 text-cyan-100",
  muted: "border-border bg-muted text-muted-foreground",
};

interface BadgeProps {
  children: ReactNode;
  className?: string;
  tone?: BadgeTone;
}

export function Badge({ children, className, tone = "default" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]",
        toneClasses[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
