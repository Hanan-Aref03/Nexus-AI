import { cn } from "@/lib/utils";

interface BrandMarkProps {
  className?: string;
  compact?: boolean;
}

export function BrandMark({ className, compact = false }: BrandMarkProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl border border-primary/30 bg-white/5 shadow-[0_0_0_1px_rgba(255,255,255,0.06)]">
        <div className="absolute inset-1 rounded-[1rem] bg-gradient-to-br from-primary/80 via-cyan-400/70 to-amber-400/80 opacity-80" />
        <div className="absolute inset-2 rounded-xl border border-white/20" />
        <div className="relative h-2.5 w-2.5 rounded-full bg-background shadow-[0_0_24px_rgba(45,212,191,0.85)]" />
      </div>
      {!compact ? (
        <div>
          <div className="text-sm font-semibold uppercase tracking-[0.28em] text-muted-foreground">NexusAI</div>
          <div className="text-xs text-muted-foreground">Investigation console</div>
        </div>
      ) : null}
    </div>
  );
}
