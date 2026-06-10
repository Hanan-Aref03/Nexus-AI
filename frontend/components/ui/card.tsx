import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-white/8 bg-card/80 shadow-glow backdrop-blur-xl",
        className,
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col gap-1.5 p-5 sm:p-6", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-lg font-semibold tracking-tight text-foreground", className)} {...props} />;
}

export function CardDescription({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-sm leading-6 text-muted-foreground", className)} {...props} />;
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 pb-5 sm:px-6 sm:pb-6", className)} {...props} />;
}

export function CardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("border-t border-white/8 px-5 py-4 sm:px-6", className)} {...props} />;
}

interface MetricProps {
  label: string;
  value: string;
  detail: string;
  accent: string;
  trend?: string;
  sparkline: number[];
}

export function MetricCard({ label, value, detail, accent, trend, sparkline }: MetricProps) {
  return (
    <Card className="relative overflow-hidden border-white/10">
      <div className={cn("absolute inset-x-0 top-0 h-1.5", accent)} />
      <CardHeader className="gap-3">
        <div className="flex items-center justify-between gap-4">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">{label}</p>
          {trend ? <span className="text-xs font-medium text-emerald-300">{trend}</span> : null}
        </div>
        <div className="flex items-end justify-between gap-4">
          <div>
            <div className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">{value}</div>
            <p className="mt-2 max-w-[28ch] text-sm leading-6 text-muted-foreground">{detail}</p>
          </div>
          <div className="flex h-16 items-end gap-1.5">
            {sparkline.map((value, index) => (
              <span
                key={`${label}-${index}`}
                className="w-2 rounded-full bg-white/10"
                style={{
                  height: `${Math.max(18, Math.min(64, value))}px`,
                  background: index === sparkline.length - 1 ? "hsl(var(--primary))" : "rgba(255,255,255,0.18)",
                }}
              />
            ))}
          </div>
        </div>
      </CardHeader>
    </Card>
  );
}
