"use client";

import type { StructureGraph } from "@/lib/types";

/** A tiered ownership diagram, drawn in SVG.
 *
 *  Deliberately not a force-directed graph: an ownership structure has a *direction*
 *  (owners above, holdings below), and a physics simulation destroys that reading for
 *  the sake of prettier spacing. The 3D explorer on the Architecture tab is for the
 *  system; this is for the tax structure, and they want opposite treatments.
 */
export function EntityGraph({ graph }: { graph: StructureGraph }) {
  const owners = new Set(graph.edges.map((e) => e.source));
  const owned = new Set(graph.edges.map((e) => e.target));

  const tier0 = graph.nodes.filter((n) => owners.has(n.id) && !owned.has(n.id));
  const tier1 = graph.nodes.filter((n) => owned.has(n.id));
  const orphans = graph.nodes.filter((n) => !owners.has(n.id) && !owned.has(n.id));

  const width = Math.max(720, tier1.length * 180);
  const boxW = 150;
  const boxH = 56;
  const tier0Y = 20;
  const tier1Y = 190;

  const xFor = (index: number, count: number) =>
    count === 1 ? width / 2 - boxW / 2 : (index * (width - boxW)) / (count - 1);

  const positions = new Map<string, { x: number; y: number }>();
  tier0.forEach((n, i) => positions.set(n.id, { x: xFor(i, tier0.length), y: tier0Y }));
  tier1.forEach((n, i) => positions.set(n.id, { x: xFor(i, tier1.length), y: tier1Y }));

  return (
    <div className="overflow-x-auto">
      <svg width={width} height={tier1Y + boxH + 30} className="min-w-full">
        {graph.edges.map((edge, i) => {
          const from = positions.get(edge.source);
          const to = positions.get(edge.target);
          if (!from || !to) return null;
          const x1 = from.x + boxW / 2;
          const y1 = from.y + boxH;
          const x2 = to.x + boxW / 2;
          const y2 = to.y;
          const mid = (y1 + y2) / 2;
          return (
            <g key={i}>
              <path
                d={`M ${x1} ${y1} C ${x1} ${mid}, ${x2} ${mid}, ${x2} ${y2}`}
                fill="none"
                stroke="rgb(var(--border))"
                strokeWidth={1.5}
              />
              <text
                x={(x1 + x2) / 2}
                y={mid}
                textAnchor="middle"
                className="fill-[rgb(var(--text-tertiary))] text-[10px]"
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                {edge.profits_pct.toFixed(1)}%
              </text>
            </g>
          );
        })}

        {[...tier0, ...tier1, ...orphans].map((node) => {
          const pos = positions.get(node.id);
          if (!pos) return null;
          const foreign = node.country !== "US";
          return (
            <g key={node.id} transform={`translate(${pos.x}, ${pos.y})`}>
              <rect
                width={boxW}
                height={boxH}
                rx={6}
                fill="rgb(var(--surface))"
                stroke={foreign ? "rgb(var(--accent))" : "rgb(var(--border))"}
                strokeWidth={foreign ? 1.8 : 1}
              />
              <text
                x={10}
                y={20}
                className="fill-[rgb(var(--text-primary))] text-[11px] font-medium"
              >
                {node.name.length > 22 ? `${node.name.slice(0, 21)}…` : node.name}
              </text>
              <text x={10} y={36} className="fill-[rgb(var(--text-tertiary))] text-[10px]">
                {node.country} · {node.entity_type.replace(/_/g, " ")}
              </text>
              {node.states.length ? (
                <text x={10} y={49} className="fill-[rgb(var(--text-tertiary))] text-[10px]">
                  {node.states.join(" · ")}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
