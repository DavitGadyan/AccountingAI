"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EntityGraph } from "@/components/engagement/entity-graph";

export default function ClientsPage() {
  const [clientId, setClientId] = useState<string | null>(null);
  const { data: engagements } = useQuery({
    queryKey: ["engagements"],
    queryFn: () => api.engagements(),
  });

  const clientIds = Array.from(new Set((engagements ?? []).map((e) => e.client_id)));
  const active = clientId ?? clientIds[0] ?? null;

  const { data: structure } = useQuery({
    queryKey: ["structure", active],
    queryFn: () => api.structure(active as string),
    enabled: Boolean(active),
  });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-primary">Structure</h1>
        <p className="mt-1 text-sm text-secondary">
          The ownership graph the rules engine reads. Filing obligations follow this shape
          — get an edge wrong and every determination below it is wrong.
        </p>
      </div>

      {clientIds.length > 1 ? (
        <div className="flex gap-2">
          {clientIds.map((id) => (
            <button
              key={id}
              onClick={() => setClientId(id)}
              className={
                id === active
                  ? "rounded-md bg-surface-raised px-3 py-1.5 text-sm font-medium text-primary"
                  : "rounded-md px-3 py-1.5 text-sm text-secondary hover:text-primary"
              }
            >
              {id.slice(0, 8)}
            </button>
          ))}
        </div>
      ) : null}

      {structure ? (
        <>
          <Card>
            <CardHeader
              title="Ownership graph"
              subtitle="Canadian holding companies above U.S. limited partnerships"
            />
            <CardBody>
              <EntityGraph graph={structure} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="Entities"
              action={<Badge>{structure.nodes.length}</Badge>}
            />
            <CardBody className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-surface-raised">
                    <tr>
                      {["Entity", "Type", "Country", "Property states", "K-1s"].map((h) => (
                        <th
                          key={h}
                          className="px-3 py-2 text-left text-[11px] font-medium uppercase tracking-wide text-tertiary"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {structure.nodes.map((node) => (
                      <tr key={node.id}>
                        <td className="px-3 py-2 font-medium text-primary">{node.name}</td>
                        <td className="px-3 py-2 text-secondary">
                          {node.entity_type.replace(/_/g, " ")}
                        </td>
                        <td className="px-3 py-2 text-secondary">{node.country}</td>
                        <td className="px-3 py-2">
                          <div className="flex flex-wrap gap-1">
                            {node.states.map((s) => (
                              <Badge key={s}>{s}</Badge>
                            ))}
                          </div>
                        </td>
                        <td className="tnum px-3 py-2 text-secondary">{node.k1_count || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardBody>
          </Card>
        </>
      ) : (
        <Card>
          <CardBody>
            <p className="text-sm text-tertiary">No client structure loaded.</p>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
