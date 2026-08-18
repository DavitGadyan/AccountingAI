"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { money } from "@/lib/utils";

export default function EngagementsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["engagements"],
    queryFn: () => api.engagements(),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-primary">Engagements</h1>
        <p className="mt-1 text-sm text-secondary">
          Annual U.S. filing engagements. Each one runs the same pipeline against a new
          year of documents.
        </p>
      </div>

      {isLoading ? <p className="text-sm text-tertiary">Loading…</p> : null}
      {error ? (
        <Card>
          <CardBody>
            <p className="text-sm text-blocking">
              {(error as Error).message} — is the API running on :8000?
            </p>
          </CardBody>
        </Card>
      ) : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {data?.map((engagement) => (
          <Link key={engagement.id} href={`/engagements/${engagement.id}`}>
            <Card className="transition-colors hover:border-accent/50">
              <CardHeader
                title={`Tax year ${engagement.tax_year}`}
                subtitle={engagement.is_first_year ? "First year — full structure review" : "Recurring — rolled forward"}
                action={<Badge tone="accent">{engagement.status.replace(/_/g, " ")}</Badge>}
              />
              <CardBody className="flex items-center justify-between">
                <span className="text-xs text-tertiary">Fixed fee</span>
                <span className="tnum text-sm font-medium text-primary">
                  {money(engagement.fixed_fee)}
                </span>
              </CardBody>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
