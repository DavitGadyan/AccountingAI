"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { OpenItem } from "@/lib/types";

export default function OpenItemsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data } = useQuery({ queryKey: ["open-items", id], queryFn: () => api.openItems(id) });

  const blocking = (data ?? []).filter(
    (i) => i.blocks_filing && i.status !== "resolved" && i.status !== "waived",
  );
  const other = (data ?? []).filter((i) => !blocking.includes(i));

  return (
    <div className="space-y-5">
      <p className="max-w-3xl text-sm text-secondary">
        A missing K-3 found in March costs an email. Found in November it costs an amended
        return. These checks run on every pipeline pass, not once at the end.
      </p>

      {blocking.length ? (
        <Card className="border-blocking/40">
          <CardHeader
            title="Blocking — no return can be transmitted"
            subtitle="The filing gate re-checks these at transmission, not just at approval"
            action={<Badge tone="blocking">{blocking.length}</Badge>}
          />
          <CardBody className="p-0">
            <ul className="divide-y divide-border">
              {blocking.map((item) => (
                <ItemRow key={item.id} engagementId={id} item={item} />
              ))}
            </ul>
          </CardBody>
        </Card>
      ) : (
        <Card className="border-cleared/40">
          <CardBody>
            <p className="text-sm text-cleared">
              No blocking items. Approved returns can be transmitted.
            </p>
          </CardBody>
        </Card>
      )}

      {other.length ? (
        <Card>
          <CardHeader title="Other items" action={<Badge>{other.length}</Badge>} />
          <CardBody className="p-0">
            <ul className="divide-y divide-border">
              {other.map((item) => (
                <ItemRow key={item.id} engagementId={id} item={item} />
              ))}
            </ul>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}

function ItemRow({ engagementId, item }: { engagementId: string; item: OpenItem }) {
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");
  const [open, setOpen] = useState(false);

  const update = useMutation({
    mutationFn: (status: string) =>
      api.updateOpenItem(engagementId, item.id, { status, resolution_note: note }),
    onSuccess: () => {
      setOpen(false);
      setNote("");
      queryClient.invalidateQueries();
    },
  });

  const settled = item.status === "resolved" || item.status === "waived";

  return (
    <li className="px-4 py-3">
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-primary">{item.title}</span>
            <Badge tone={item.severity === "blocking" ? "blocking" : "analysis"}>
              {item.severity}
            </Badge>
            {item.requested_from ? (
              <Badge tone="accent">from {item.requested_from}</Badge>
            ) : null}
            {settled ? <Badge tone="cleared">{item.status}</Badge> : null}
          </div>
          <p className="mt-1 max-w-3xl text-sm leading-relaxed text-secondary">{item.detail}</p>
          {item.resolution_note ? (
            <p className="mt-1.5 rounded bg-surface-raised px-2 py-1 text-xs text-tertiary">
              {item.resolution_note}
            </p>
          ) : null}
        </div>

        {!settled ? (
          <Button variant="outline" size="sm" onClick={() => setOpen(!open)}>
            {open ? "Cancel" : "Resolve"}
          </Button>
        ) : null}
      </div>

      {open ? (
        <div className="mt-3 space-y-2 rounded-md border border-border p-3">
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            placeholder="How was this resolved? A note is required — an item cleared without one is indistinguishable from one ignored."
            className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-primary placeholder:text-tertiary"
          />
          <div className="flex gap-2">
            <Button size="sm" disabled={!note.trim()} onClick={() => update.mutate("resolved")}>
              Mark resolved
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={!note.trim()}
              onClick={() => update.mutate("waived")}
            >
              Waive (reviewer only)
            </Button>
          </div>
          {update.error ? (
            <p className="text-xs text-blocking">{(update.error as Error).message}</p>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}
