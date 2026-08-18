"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const TABS = [
  { slug: "", label: "Overview" },
  { slug: "documents", label: "Documents & extraction" },
  { slug: "determinations", label: "Determinations" },
  { slug: "workpapers", label: "Workpapers" },
  { slug: "open-items", label: "Open items" },
  { slug: "filings", label: "Filings" },
];

export default function EngagementLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const pathname = usePathname();
  const { data } = useQuery({
    queryKey: ["dashboard", id],
    queryFn: () => api.dashboard(id),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-primary">
            {data?.client_name ?? "Engagement"}
          </h1>
          <p className="mt-0.5 text-sm text-secondary">
            Tax year {data?.engagement.tax_year ?? "—"} · U.S. federal, state and
            international filings
          </p>
        </div>
        {data && data.open_items_blocking > 0 ? (
          <Badge tone="blocking">
            {data.open_items_blocking} blocking item
            {data.open_items_blocking === 1 ? "" : "s"}
          </Badge>
        ) : null}
      </div>

      <nav className="flex gap-1 overflow-x-auto border-b border-border">
        {TABS.map((tab) => {
          const href = `/engagements/${id}${tab.slug ? `/${tab.slug}` : ""}`;
          const active = tab.slug
            ? pathname.startsWith(href)
            : pathname === `/engagements/${id}`;
          return (
            <Link
              key={tab.slug}
              href={href}
              className={cn(
                "whitespace-nowrap border-b-2 px-3 py-2 text-sm transition-colors",
                active
                  ? "border-accent font-medium text-primary"
                  : "border-transparent text-secondary hover:text-primary",
              )}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>

      {children}
    </div>
  );
}
