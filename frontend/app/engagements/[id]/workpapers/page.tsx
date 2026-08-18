"use client";

import { use, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn, money } from "@/lib/utils";

export default function WorkpapersPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [active, setActive] = useState<string | null>(null);
  const { data } = useQuery({ queryKey: ["workpapers", id], queryFn: () => api.workpapers(id) });

  const selected = data?.find((w) => w.id === active) ?? data?.[0];

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,280px)_minmax(0,1fr)]">
      <Card className="h-fit">
        <CardHeader title="Schedules" subtitle="Regenerated from the fact base on every run" />
        <CardBody className="p-0">
          <ul className="divide-y divide-border">
            {data?.map((wp) => (
              <li key={wp.id}>
                <button
                  onClick={() => setActive(wp.id)}
                  className={cn(
                    "w-full px-4 py-2.5 text-left transition-colors hover:bg-surface-raised",
                    selected?.id === wp.id && "bg-surface-raised",
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] text-tertiary">{wp.code}</span>
                    {!wp.ties_out ? <Badge tone="blocking">Does not tie</Badge> : null}
                  </div>
                  <p className="mt-0.5 truncate text-sm text-primary">{wp.title}</p>
                </button>
              </li>
            ))}
          </ul>
        </CardBody>
      </Card>

      {selected ? (
        <Card>
          <CardHeader
            title={selected.title}
            subtitle={selected.code}
            action={
              selected.ties_out ? (
                <Badge tone="cleared">Ties out</Badge>
              ) : (
                <Badge tone="blocking">Does not tie out</Badge>
              )
            }
          />
          <CardBody className="space-y-4">
            {selected.narrative ? (
              <p className="max-w-3xl text-sm leading-relaxed text-secondary">
                {selected.narrative}
              </p>
            ) : null}

            {selected.rows.length ? (
              <div className="overflow-x-auto rounded-md border border-border">
                <table className="w-full text-sm">
                  <thead className="bg-surface-raised">
                    <tr>
                      {Object.keys(selected.rows[0]).map((key) => (
                        <th
                          key={key}
                          className={cn(
                            "px-3 py-2 text-[11px] font-medium uppercase tracking-wide text-tertiary",
                            key === "amount" ? "text-right" : "text-left",
                          )}
                        >
                          {key.replace(/_/g, " ")}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {selected.rows.map((row, i) => (
                      <tr key={i}>
                        {Object.entries(row).map(([key, value]) => (
                          <td
                            key={key}
                            className={cn(
                              "px-3 py-2",
                              key === "amount"
                                ? "tnum text-right text-primary"
                                : "text-secondary",
                            )}
                          >
                            {key === "amount" && typeof value === "number"
                              ? money(value)
                              : typeof value === "boolean"
                                ? value
                                  ? "Yes"
                                  : "No"
                                : String(value ?? "—")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            {Object.keys(selected.totals).length ? (
              <div className="grid gap-x-8 gap-y-1.5 sm:grid-cols-2">
                {Object.entries(selected.totals).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-baseline justify-between gap-4 border-b border-border pb-1"
                  >
                    <span className="text-xs text-tertiary">{key.replace(/_/g, " ")}</span>
                    <span className="tnum text-sm font-medium text-primary">
                      {typeof value === "number" && Math.abs(value) > 100
                        ? money(value)
                        : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            ) : null}
          </CardBody>
        </Card>
      ) : (
        <Card>
          <CardBody>
            <p className="text-sm text-tertiary">
              No workpapers yet — run the determination pipeline from the overview tab.
            </p>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
