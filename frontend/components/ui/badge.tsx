import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type Tone =
  | "neutral"
  | "required"
  | "protective"
  | "analysis"
  | "cleared"
  | "blocking"
  | "accent";

const tones: Record<Tone, string> = {
  neutral: "bg-surface-raised text-secondary border-border",
  required: "bg-required/10 text-required border-required/30",
  protective: "bg-protective/10 text-protective border-protective/30",
  analysis: "bg-analysis/10 text-analysis border-analysis/30",
  cleared: "bg-cleared/10 text-cleared border-cleared/30",
  blocking: "bg-blocking/10 text-blocking border-blocking/30",
  accent: "bg-accent/10 text-accent border-accent/30",
};

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium leading-4",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

/** Requirement values carry legal meaning, so the mapping lives in one place. */
export function requirementTone(requirement: string): Tone {
  switch (requirement) {
    case "required":
      return "required";
    case "protective":
      return "protective";
    case "needs_analysis":
      return "analysis";
    case "not_required":
      return "cleared";
    default:
      return "neutral";
  }
}

export function requirementLabel(requirement: string): string {
  switch (requirement) {
    case "required":
      return "Required";
    case "protective":
      return "Protective";
    case "needs_analysis":
      return "Needs analysis";
    case "not_required":
      return "Not required";
    case "recommended":
      return "Recommended";
    default:
      return requirement;
  }
}
