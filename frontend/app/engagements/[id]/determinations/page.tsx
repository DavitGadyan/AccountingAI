"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Badge, requirementLabel, requirementTone } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn, percent, shortDate } from "@/lib/utils";
import type { Determination } from "@/lib/types";

const GROUPS: { key: string; label: string; blurb: string }[] = [
  {
    key: "us_federal",
    label: "U.S. federal",
    blurb: "Returns and information returns filed with the IRS",
  },
  {
    key: "us_state",
    label: "State",
    blurb: "Driven by where the property sits, not where the partnership was formed",
  },
  {
    key: "canada_federal",
    label: "Canadian advisory",
    blurb: "Outside this engagement's scope — flagged for the client's Canadian accountant",
  },
];

export default function DeterminationsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [expanded, setExpanded] = useState<string | null>(null);
  const { data } = useQuery({
    queryKey: ["determinations", id],
    queryFn: () => api.determinations(id),
  });
  // The rule set is versioned by the engagement's tax year, not by today's date —
  // re-opening a 2025 engagement in 2031 must still say 2025.
  const { data: dashboard } = useQuery({
    queryKey: ["dashboard", id],
    queryFn: () => api.dashboard(id),
  });

  return (
    <div className="space-y-5">
      <p className="max-w-3xl text-sm text-secondary">
        Every rule in the {dashboard?.engagement.tax_year ?? ""} rule set is evaluated
        against the entity structure. Conclusions of <em>not required</em> are shown
        alongside the required filings — a documented negative is a deliverable, and it is
        what makes next year a comparison rather than a fresh analysis.
      </p>

      {GROUPS.map((group) => {
        const rows = (data ?? []).filter((d) => d.jurisdiction === group.key);
        if (!rows.length) return null;
        return (
          <Card key={group.key}>
            <CardHeader
              title={group.label}
              subtitle={group.blurb}
              action={<Badge>{rows.length}</Badge>}
            />
            <CardBody className="p-0">
              <ul className="divide-y divide-border">
                {rows.map((d) => (
                  <DeterminationRow
                    key={d.id}
                    engagementId={id}
                    determination={d}
                    expanded={expanded === d.id}
                    onToggle={() => setExpanded(expanded === d.id ? null : d.id)}
                  />
                ))}
              </ul>
            </CardBody>
          </Card>
        );
      })}
    </div>
  );
}

function DeterminationRow({
  engagementId,
  determination: d,
  expanded,
  onToggle,
}: {
  engagementId: string;
  determination: Determination;
  expanded: boolean;
  onToggle: () => void;
}) {
  const queryClient = useQueryClient();
  const [overriding, setOverriding] = useState(false);
  const [reason, setReason] = useState("");
  const [requirement, setRequirement] = useState("not_required");

  const override = useMutation({
    mutationFn: () =>
      api.overrideDetermination(engagementId, d.id, { requirement, reason }),
    onSuccess: () => {
      setOverriding(false);
      setReason("");
      queryClient.invalidateQueries({ queryKey: ["determinations", engagementId] });
    },
  });

  const effective = d.override_requirement ?? d.requirement;

  return (
    <li className="px-4 py-3">
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-3 text-left"
        aria-expanded={expanded}
      >
        <Badge tone={requirementTone(effective)}>{requirementLabel(effective)}</Badge>
        <span className="text-sm font-medium text-primary">{d.form}</span>
        {d.state ? <Badge>{d.state}</Badge> : null}
        {d.override_requirement ? <Badge tone="accent">Reviewer override</Badge> : null}
        {d.confidence < 0.9 ? (
          <span className="text-xs text-tertiary">{percent(d.confidence, 0)} confidence</span>
        ) : null}
        <span className="ml-auto tnum text-xs text-tertiary">
          {shortDate(d.extended_due_date ?? d.due_date)}
        </span>
        <span className={cn("text-tertiary transition-transform", expanded && "rotate-90")}>
          ›
        </span>
      </button>

      {expanded ? (
        <div className="mt-3 space-y-3 border-l-2 border-border pl-4">
          <p className="text-sm leading-relaxed text-secondary">{d.rationale}</p>

          <div className="rounded-md bg-surface-raised px-3 py-2">
            <p className="text-[11px] uppercase tracking-wide text-tertiary">Authority</p>
            <p className="mt-0.5 font-mono text-xs text-secondary">{d.authority}</p>
          </div>

          {Object.keys(d.triggering_facts).length ? (
            <div>
              <p className="text-[11px] uppercase tracking-wide text-tertiary">
                Facts that triggered this
              </p>
              <dl className="mt-1 grid gap-x-6 gap-y-1 sm:grid-cols-2">
                {Object.entries(d.triggering_facts).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-3 text-xs">
                    <dt className="text-tertiary">{key.replace(/_/g, " ")}</dt>
                    <dd className="tnum text-secondary">{String(value)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ) : null}

          {d.override_reason ? (
            <div className="rounded-md border border-accent/30 bg-accent/5 px-3 py-2">
              <p className="text-[11px] uppercase tracking-wide text-accent">
                Reviewer override
              </p>
              <p className="mt-0.5 text-xs text-secondary">{d.override_reason}</p>
            </div>
          ) : null}

          <div className="flex items-center gap-2 pt-1">
            <span className="font-mono text-[11px] text-tertiary">
              {d.rule_id} · {d.rule_version}
            </span>
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto"
              onClick={() => setOverriding(!overriding)}
            >
              {overriding ? "Cancel" : "Override"}
            </Button>
          </div>

          {overriding ? (
            <div className="space-y-2 rounded-md border border-border p-3">
              <select
                value={requirement}
                onChange={(e) => setRequirement(e.target.value)}
                className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-primary"
              >
                <option value="required">Required</option>
                <option value="protective">Protective</option>
                <option value="not_required">Not required</option>
                <option value="needs_analysis">Needs analysis</option>
              </select>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={3}
                placeholder="Why does the engine's conclusion not hold here? This appears in the client memo and survives every re-run."
                className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-primary placeholder:text-tertiary"
              />
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  disabled={reason.trim().length < 20 || override.isPending}
                  onClick={() => override.mutate()}
                >
                  Record override
                </Button>
                {reason.trim().length < 20 ? (
                  <span className="text-xs text-tertiary">
                    A reason of at least 20 characters is required
                  </span>
                ) : null}
              </div>
              {override.error ? (
                <p className="text-xs text-blocking">{(override.error as Error).message}</p>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}
