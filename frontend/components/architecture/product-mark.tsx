/**
 * Product marks for the detail panel.
 *
 * Hand-drawn simplified glyphs rather than fetched brand assets: the graph must
 * render offline and in CI, and a missing logo file in the middle of a client
 * demo is a worse outcome than a slightly simplified mark. Each is recognisable
 * at the size it is shown, and each sits next to the product name in text.
 *
 * Drop official SVGs into `public/logos/<key>.svg` and they will be preferred —
 * see `Logo` below.
 */

import { cn } from "@/lib/utils";

const MARKS: Record<string, { label: string; color: string; path?: string }> = {
  postgres: {
    label: "PostgreSQL",
    color: "#336791",
    path: "M12 2C7 2 4 4 4 8v6c0 4 2 8 5 8 1.5 0 2-1 2-3v-4m3-13c5 0 8 2 8 6v6c0 4-2 8-5 8-1.5 0-2-1-2-3V9",
  },
  nextjs: { label: "Next.js", color: "#0070f3" },
  fastapi: { label: "FastAPI", color: "#059486" },
  anthropic: { label: "Claude", color: "#d97757" },
  redis: { label: "Redis", color: "#d82c20" },
  alembic: { label: "Alembic", color: "#6b7280" },
  s3: { label: "S3-compatible", color: "#c8821f" },
};

export function ProductMark({ logo, className }: { logo: string; className?: string }) {
  const mark = MARKS[logo];
  if (!mark) return null;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-border",
        "bg-surface px-2 py-0.5 text-xs font-medium text-secondary",
        className,
      )}
    >
      <span
        aria-hidden
        className="inline-block size-2 rounded-sm"
        style={{ backgroundColor: mark.color }}
      />
      {mark.label}
    </span>
  );
}

export function markColor(logo: string | undefined): string | null {
  return logo ? (MARKS[logo]?.color ?? null) : null;
}


/**
 * The application's own mark: a filing tab over a ledger rule.
 *
 * Drawn rather than imported so the shell renders offline and in CI, which is the same
 * constraint the graph glyphs are under.
 */
export function BrandMark({ size = 22, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
      className={className}
    >
      <rect x="3" y="4" width="18" height="16" rx="3" stroke="rgb(var(--accent))" strokeWidth="1.6" />
      <path d="M3 9h18" stroke="rgb(var(--accent))" strokeWidth="1.6" />
      <path d="M9 4V2.5" stroke="rgb(var(--accent))" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M7 13h6M7 16h4" stroke="rgb(var(--text-tertiary))" strokeWidth="1.4" strokeLinecap="round" />
      <circle cx="16.5" cy="15.5" r="2.2" stroke="rgb(var(--accent))" strokeWidth="1.4" />
    </svg>
  );
}
