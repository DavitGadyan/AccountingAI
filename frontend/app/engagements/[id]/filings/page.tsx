"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { shortDate } from "@/lib/utils";
import type { Filing } from "@/lib/types";

const STATUS_TONE: Record<string, "neutral" | "accent" | "cleared" | "blocking" | "analysis"> = {
  not_started: "neutral",
  in_preparation: "neutral",
  ready_for_review: "analysis",
  approved: "accent",
  transmitted: "accent",
  accepted: "cleared",
  rejected: "blocking",
};

export default function FilingsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data } = useQuery({ queryKey: ["filings", id], queryFn: () => api.filings(id) });

  const federal = (data ?? []).filter((f) => f.jurisdiction === "us_federal");
  const state = (data ?? []).filter((f) => f.jurisdiction === "us_state");

  return (
    <div className="space-y-5">
      <p className="max-w-3xl text-sm text-secondary">
        Approval requires a credentialed CPA or EA, and transmission re-checks every gate
        condition rather than trusting the approval — an open item can be reopened between
        the two.
      </p>

      {[
        { label: "U.S. federal", rows: federal },
        { label: "State", rows: state },
      ].map(({ label, rows }) =>
        rows.length ? (
          <Card key={label}>
            <CardHeader title={label} action={<Badge>{rows.length}</Badge>} />
            <CardBody className="p-0">
              <ul className="divide-y divide-border">
                {rows.map((filing) => (
                  <FilingRow key={filing.id} engagementId={id} filing={filing} />
                ))}
              </ul>
            </CardBody>
          </Card>
        ) : null,
      )}

      {!data?.length ? (
        <Card>
          <CardBody>
            <p className="text-sm text-tertiary">
              No filings yet. Run the determination pipeline to create them.
            </p>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}

function FilingRow({ engagementId, filing }: { engagementId: string; filing: Filing }) {
  const queryClient = useQueryClient();
  const [showGate, setShowGate] = useState(false);

  const { data: gate } = useQuery({
    queryKey: ["gate", filing.id],
    queryFn: () => api.gate(engagementId, filing.id),
    enabled: showGate,
  });

  const approve = useMutation({
    mutationFn: () => api.approveFiling(engagementId, filing.id),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const transmit = useMutation({
    mutationFn: () => api.transmitFiling(engagementId, filing.id),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const transmitError = transmit.error as ApiError | null;

  return (
    <li className="px-4 py-3">
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm font-medium text-primary">{filing.form}</span>
        {filing.state ? <Badge>{filing.state}</Badge> : null}
        {filing.is_protective ? <Badge tone="protective">Protective</Badge> : null}
        {filing.is_extension ? <Badge tone="accent">Extension</Badge> : null}
        <Badge tone={STATUS_TONE[filing.status] ?? "neutral"}>
          {filing.status.replace(/_/g, " ")}
        </Badge>

        {filing.submission_id ? (
          <span className="font-mono text-[11px] text-tertiary">{filing.submission_id}</span>
        ) : null}
        {filing.approved_at ? (
          <span className="text-xs text-secondary">
            Signed {shortDate(filing.approved_at)}
          </span>
        ) : null}
        {filing.acknowledged_at ? (
          <span className="text-xs text-cleared">
            Accepted {shortDate(filing.acknowledged_at)}
          </span>
        ) : null}

        <div className="ml-auto flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setShowGate(!showGate)}>
            {showGate ? "Hide gate" : "Check gate"}
          </Button>
          {filing.status !== "accepted" ? (
            <>
              <Button
                variant="outline"
                size="sm"
                disabled={approve.isPending || filing.status === "approved"}
                onClick={() => approve.mutate()}
              >
                Approve
              </Button>
              <Button
                size="sm"
                disabled={transmit.isPending || filing.status !== "approved"}
                onClick={() => transmit.mutate()}
              >
                Transmit
              </Button>
            </>
          ) : null}
        </div>
      </div>

      {approve.error ? (
        <p className="mt-2 text-xs text-blocking">{(approve.error as Error).message}</p>
      ) : null}

      {transmitError ? (
        <div className="mt-2 rounded-md border border-blocking/40 bg-blocking/5 px-3 py-2">
          <p className="text-xs font-medium text-blocking">{transmitError.message}</p>
          <ul className="mt-1 space-y-0.5">
            {transmitError.blockers.map((blocker) => (
              <li key={blocker} className="text-xs text-secondary">
                · {blocker}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {showGate && gate ? (
        <div className="mt-2 rounded-md border border-border bg-surface-raised px-3 py-2">
          {gate.transmittable ? (
            <p className="text-xs text-cleared">
              All gate conditions satisfied — this return may be transmitted.
            </p>
          ) : (
            <ul className="space-y-0.5">
              {gate.blockers.map((blocker) => (
                <li key={blocker} className="text-xs text-secondary">
                  · {blocker}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      {filing.reject_codes?.length ? (
        <p className="mt-2 font-mono text-xs text-blocking">
          Reject codes: {filing.reject_codes.join(", ")}
        </p>
      ) : null}
    </li>
  );
}
