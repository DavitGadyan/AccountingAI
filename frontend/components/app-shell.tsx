"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSyncExternalStore } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  applyTheme,
  getResolvedServerSnapshot,
  getResolvedSnapshot,
  subscribeResolved,
} from "@/lib/theme-store";
import { BrandMark } from "@/components/architecture/product-mark";

const NAV = [
  { href: "/", label: "Engagements" },
  { href: "/clients", label: "Clients" },
  { href: "/architecture", label: "Architecture" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const resolved = useSyncExternalStore(
    subscribeResolved,
    getResolvedSnapshot,
    getResolvedServerSnapshot,
  );

  if (pathname === "/login") return <>{children}</>;

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-border bg-surface/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-6 px-6">
          <Link href="/" className="flex items-center gap-2">
            <BrandMark size={22} />
            <span className="text-sm font-semibold tracking-tight text-primary">
              AccountingAI
            </span>
          </Link>

          <nav className="flex items-center gap-1">
            {NAV.map((item) => {
              const active =
                item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-sm transition-colors",
                    active
                      ? "bg-surface-raised font-medium text-primary"
                      : "text-secondary hover:text-primary",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Toggle theme"
              onClick={() => applyTheme(resolved === "dark" ? "light" : "dark")}
            >
              {resolved === "dark" ? "☀" : "☾"}
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1400px] px-6 py-6">{children}</main>
    </div>
  );
}
