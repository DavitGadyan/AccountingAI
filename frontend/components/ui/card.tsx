import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-lg border border-border bg-surface", className)}>{children}</div>
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border px-4 py-3">
      <div className="min-w-0">
        <h2 className="text-sm font-semibold text-primary">{title}</h2>
        {subtitle ? <p className="mt-0.5 text-xs text-tertiary">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function CardBody({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("px-4 py-3", className)}>{children}</div>;
}

export function Metric({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: "default" | "warn" | "good";
}) {
  return (
    <div className="rounded-lg border border-border bg-surface px-4 py-3">
      <p className="text-[11px] uppercase tracking-wide text-tertiary">{label}</p>
      <p
        className={cn(
          "tnum mt-1 text-2xl font-semibold",
          tone === "warn" && "text-blocking",
          tone === "good" && "text-cleared",
          (!tone || tone === "default") && "text-primary",
        )}
      >
        {value}
      </p>
      {hint ? <p className="mt-1 text-xs text-tertiary">{hint}</p> : null}
    </div>
  );
}
