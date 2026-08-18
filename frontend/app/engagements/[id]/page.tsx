"use client";

import Link from "next/link";
import { use } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader, Metric } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge, requirementLabel, requirementTone } from "@/components/ui/badge";
import { daysUntil, shortDate } from "@/lib/utils";

export default function OverviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const queryClient = useQueryClient();

  const { data } = useQuery({ queryKey: ["dashboard", id], queryFn: () => api.dashboard(id) });
  const { data: determinations } = useQuery({
    queryKey: ["determinations", id],
    queryFn: () => api.determinations(id),
  });
  const { data: variances } = useQuery({
    queryKey: ["variances", id],
    queryFn: () => api.variances(id),
  });

  const determine = useMutation({
    mutationFn: () => api.determine(id),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const due = daysUntil(data?.next_due_date);
  const upcoming = (determinations ?? [])
    .filter((d) => d.requirement === "required" || d.requirement === "protective")
    .sort((a, b) =>
      (a.extended_due_date ?? a.due_date ?? "") > (b.extended_due_date ?? b.due_date ?? "")
        ? 1
        : -1,
    )
    .slice(0, 6);

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          label="Documents received"
          value={`${data?.documents_received ?? 0} / ${data?.documents_expected ?? 0}`}
          hint="One K-1 and one K-3 expected per syndication"
          tone={
            data && data.documents_received < data.documents_expected ? "warn" : "good"
          }
        />
        <Metric
          label="Fields awaiting review"
          value={data?.fields_needing_review ?? 0}
          hint="Extractions below the confidence threshold"
        />
        <Metric
          label="Filings required"
          value={data?.filings_required ?? 0}
          hint={`${data?.filings_accepted ?? 0} accepted by the IRS`}
        />
        <Metric
          label="Next deadline"
          value={due === null ? "—" : `${due}d`}
          hint={shortDate(data?.next_due_date)}
          tone={due !== null && due < 21 ? "warn" : "default"}
        />
      </div>

      {data && data.open_items_blocking > 0 ? (
        <Card className="border-blocking/40">
          <CardBody className="flex items-center justify-between gap-4">
            <p className="text-sm text-primary">
              <span className="font-semibold text-blocking">
                {data.open_items_blocking} blocking open item
                {data.open_items_blocking === 1 ? "" : "s"}
              </span>{" "}
              — no return can be transmitted until these are resolved or waived by a
              reviewer.
            </p>
            <Link
              href={`/engagements/${id}/open-items`}
              className="shrink-0 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-primary hover:bg-surface-raised"
            >
              Review
            </Link>
          </CardBody>
        </Card>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Determination pipeline"
            subtitle="Deterministic rules over the entity graph — same facts, same forms, every year"
            action={
              <Button
                size="sm"
                onClick={() => determine.mutate()}
                disabled={determine.isPending}
              >
                {determine.isPending ? "Running…" : "Run determination"}
              </Button>
            }
          />
          <CardBody className="space-y-3">
            {determine.data ? (
              <div className="rounded-md border border-border bg-surface-raised px-3 py-2 text-xs text-secondary">
                Evaluated {determine.data.rules_evaluated} rules ·{" "}
                {determine.data.determinations} determinations ·{" "}
                {determine.data.workpapers_generated} workpapers ·{" "}
                {determine.data.blocking_items} blocking items
              </div>
            ) : null}

            {upcoming.length === 0 ? (
              <p className="text-sm text-tertiary">
                No determinations yet. Run the pipeline once the K-1s are in.
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {upcoming.map((d) => (
                  <li key={d.id} className="flex items-center gap-3 py-2">
                    <Badge tone={requirementTone(d.requirement)}>
                      {requirementLabel(d.requirement)}
                    </Badge>
                    <span className="text-sm font-medium text-primary">{d.form}</span>
                    {d.state ? <Badge>{d.state}</Badge> : null}
                    <span className="ml-auto tnum text-xs text-tertiary">
                      {shortDate(d.extended_due_date ?? d.due_date)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title="Changed since last year"
            subtitle="Every material movement needs a sentence before signing"
          />
          <CardBody>
            {!variances?.length ? (
              <p className="text-sm text-tertiary">
                Nothing material moved — or there is no prior year to compare against.
              </p>
            ) : (
              <ul className="space-y-3">
                {variances.slice(0, 5).map((v) => (
                  <li key={v.id}>
                    <p className="text-xs font-medium uppercase tracking-wide text-tertiary">
                      {v.metric.replace(/_/g, " ")}
                    </p>
                    <p className="mt-0.5 text-sm text-secondary">{v.explanation}</p>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
