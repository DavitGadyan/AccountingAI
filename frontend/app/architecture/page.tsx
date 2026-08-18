import { ArchitectureExplorer } from "@/components/architecture/architecture-explorer";

export const metadata = {
  title: "Architecture — AccountingAI",
  description:
    "How a folder of K-1 PDFs becomes a filed, cited, defensible set of U.S. returns.",
};

/**
 * Architecture tab.
 *
 * Entirely static content — no API call, no query client. This page has to render with
 * the backend stopped, because it gets shown live to people making a buying decision and
 * a demo that fails on a cold service is a demo that failed for no reason.
 */
export default function ArchitecturePage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-primary">
          How the system works
        </h1>
        <p className="mt-1 max-w-3xl text-sm text-secondary">
          Eight stages, in the order an engagement travels: five K-1 PDFs arrive from five
          syndicators, and a filed, cited set of U.S. federal, state and international
          returns comes out. Click any stage to open it; every component says what it does,
          what breaks without it, what it saves the firm and what the investor feels.
        </p>
      </div>

      {/* The explorer sizes its canvas from this container via a ResizeObserver, so the
          height has to be definite. Left to `auto` the canvas keeps its 800×600 fallback,
          the graph's centre lands below the fold, and the stages render clipped and
          overlapping — which is exactly the failure this page cannot afford on camera. */}
      <div className="h-[calc(100vh-14rem)] min-h-[600px] overflow-hidden rounded-lg border border-border bg-surface">
        <ArchitectureExplorer />
      </div>
    </div>
  );
}
