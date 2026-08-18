"use client";

import { use, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn, percent, shortDate } from "@/lib/utils";
import type { ExtractedField, TaxDocument } from "@/lib/types";

const KIND_LABELS: Record<string, string> = {
  k1_1065: "Schedule K-1",
  k3_1065: "Schedule K-3",
  form_8805: "Form 8805",
  form_1042s: "Form 1042-S",
  form_8288a: "Form 8288-A",
  prior_year_return: "Prior-year return",
  prior_year_workpaper: "Prior-year workpaper",
  state_supplement: "State supplement",
  unclassified: "Unclassified",
};

export default function DocumentsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const queryClient = useQueryClient();
  const fileInput = useRef<HTMLInputElement>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const { data: documents } = useQuery({
    queryKey: ["documents", id],
    queryFn: () => api.documents(id),
  });

  const upload = useMutation({
    mutationFn: (file: File) => api.uploadDocument(id, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents", id] }),
  });

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,400px)_minmax(0,1fr)]">
      <Card className="h-fit">
        <CardHeader
          title="Documents"
          subtitle="Deduplicated on content hash — the same K-1 sent twice is not extracted twice"
          action={
            <Button size="sm" onClick={() => fileInput.current?.click()}>
              Upload
            </Button>
          }
        />
        <CardBody className="p-0">
          <input
            ref={fileInput}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) upload.mutate(file);
              e.target.value = "";
            }}
          />

          {upload.error ? (
            <p className="px-4 py-2 text-xs text-blocking">
              {(upload.error as Error).message}
            </p>
          ) : null}

          {!documents?.length ? (
            <p className="px-4 py-6 text-sm text-tertiary">
              No documents yet. Upload the K-1s as they arrive from each syndicator.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {documents.map((doc) => (
                <li key={doc.id}>
                  <button
                    onClick={() => setSelected(doc.id)}
                    className={cn(
                      "w-full px-4 py-3 text-left transition-colors hover:bg-surface-raised",
                      selected === doc.id && "bg-surface-raised",
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-primary">
                        {doc.filename}
                      </span>
                      {doc.is_amended ? <Badge tone="protective">Amended</Badge> : null}
                    </div>
                    <div className="mt-1 flex items-center gap-2">
                      <Badge tone={doc.status === "accepted" ? "cleared" : "neutral"}>
                        {KIND_LABELS[doc.kind] ?? doc.kind}
                      </Badge>
                      <span className="text-xs text-tertiary">
                        {doc.status.replace(/_/g, " ")}
                      </span>
                      <span className="ml-auto text-xs text-tertiary">
                        {shortDate(doc.created_at)}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      {selected ? (
        <ExtractionReview engagementId={id} documentId={selected} documents={documents ?? []} />
      ) : (
        <Card>
          <CardBody>
            <p className="text-sm text-tertiary">
              Select a document to review its extracted values.
            </p>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function ExtractionReview({
  engagementId,
  documentId,
  documents,
}: {
  engagementId: string;
  documentId: string;
  documents: TaxDocument[];
}) {
  const queryClient = useQueryClient();
  const [onlyUnreviewed, setOnlyUnreviewed] = useState(true);

  const { data: fields } = useQuery({
    queryKey: ["fields", documentId, onlyUnreviewed],
    queryFn: () => api.fields(engagementId, documentId, onlyUnreviewed),
  });

  const doc = documents.find((d) => d.id === documentId);
  const review = useMutation({
    mutationFn: (args: { fieldId: string; confirmed: boolean; corrected?: number }) =>
      api.reviewField(engagementId, args.fieldId, {
        confirmed: args.confirmed,
        corrected_value: args.corrected,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fields", documentId] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", engagementId] });
    },
  });

  return (
    <Card>
      <CardHeader
        title={doc?.filename ?? "Extraction"}
        subtitle="Every value shows the page it came from — review should be a glance, not a hunt"
        action={
          <Button variant="outline" size="sm" onClick={() => setOnlyUnreviewed(!onlyUnreviewed)}>
            {onlyUnreviewed ? "Show all fields" : "Only needs review"}
          </Button>
        }
      />
      <CardBody className="p-0">
        {!fields?.length ? (
          <p className="px-4 py-6 text-sm text-tertiary">
            {onlyUnreviewed
              ? "Nothing awaiting review on this document."
              : "No extraction has run for this document yet."}
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {fields.map((field) => (
              <FieldRow
                key={field.id}
                field={field}
                onConfirm={() => review.mutate({ fieldId: field.id, confirmed: true })}
                onCorrect={(value) =>
                  review.mutate({ fieldId: field.id, confirmed: false, corrected: value })
                }
              />
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

function FieldRow({
  field,
  onConfirm,
  onCorrect,
}: {
  field: ExtractedField;
  onConfirm: () => void;
  onCorrect: (value: number) => void;
}) {
  const [draft, setDraft] = useState<string>(
    field.corrected_value?.toString() ?? field.numeric_value?.toString() ?? "",
  );
  const pending = field.status === "needs_review";
  const lowConfidence = field.confidence < 0.9;

  return (
    <li className="px-4 py-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-primary">{field.label}</p>
          <p className="mt-0.5 font-mono text-[11px] text-tertiary">
            {field.field_path}
            {field.page ? ` · page ${field.page}` : ""}
          </p>
        </div>

        <Badge
          tone={
            field.status === "corrected"
              ? "protective"
              : field.status === "needs_review"
                ? "analysis"
                : "cleared"
          }
        >
          {field.status.replace(/_/g, " ")}
        </Badge>

        <span
          className={cn("tnum text-xs", lowConfidence ? "text-blocking" : "text-tertiary")}
          title="Model confidence for this specific field"
        >
          {percent(field.confidence, 0)}
        </span>

        {pending ? (
          <div className="flex items-center gap-2">
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="tnum w-32 rounded border border-border bg-surface px-2 py-1 text-right text-sm text-primary"
            />
            <Button size="sm" variant="outline" onClick={onConfirm}>
              Confirm
            </Button>
            <Button
              size="sm"
              onClick={() => onCorrect(Number(draft))}
              disabled={Number.isNaN(Number(draft))}
            >
              Correct
            </Button>
          </div>
        ) : (
          <span className="tnum w-32 text-right text-sm text-primary">
            {field.corrected_value ?? field.numeric_value ?? field.raw_value ?? "—"}
          </span>
        )}
      </div>

      {field.source_text ? (
        <p className="mt-2 rounded bg-surface-raised px-2 py-1 font-mono text-[11px] text-tertiary">
          {field.source_text}
        </p>
      ) : null}
    </li>
  );
}
