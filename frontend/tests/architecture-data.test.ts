import { describe, expect, it } from "vitest";

import {
  ancestorsOf,
  CHILDREN_BY_PARENT,
  LINKS,
  NODES,
  NODE_BY_ID,
  ROOT_ID,
  STAGES,
  TIERS,
  TIER_BY_ID,
  TOUR,
  TREE_LINKS,
} from "@/lib/architecture-data";

/**
 * The architecture graph is demo content, and demo content rots silently: a renamed node
 * id breaks a tour step, a missing rationale field renders an empty panel, and neither
 * shows up until someone is recording.
 *
 * These tests are the guard. They run with nothing else running — no API, no database,
 * no network — which is the same property the page itself has to have.
 */

describe("architecture graph integrity", () => {
  it("has unique node ids", () => {
    const ids = NODES.map((n) => n.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("every link connects two real nodes", () => {
    for (const link of LINKS) {
      expect(NODE_BY_ID.has(link.source), `unknown source: ${link.source}`).toBe(true);
      expect(NODE_BY_ID.has(link.target), `unknown target: ${link.target}`).toBe(true);
    }
  });

  it("every node belongs to a declared tier", () => {
    for (const node of NODES) {
      expect(TIER_BY_ID.has(node.tier), `${node.id} has tier ${node.tier}`).toBe(true);
    }
  });

  it("every tier is populated", () => {
    for (const tier of TIERS) {
      expect(
        NODES.some((n) => n.tier === tier.id),
        `tier "${tier.id}" has no nodes`,
      ).toBe(true);
    }
  });

  it("no node is orphaned", () => {
    const connected = new Set(
      [...LINKS, ...TREE_LINKS].flatMap((l) => [l.source, l.target]),
    );
    for (const node of NODES) {
      if (node.id === ROOT_ID) continue;
      expect(connected.has(node.id), `${node.id} is not connected to anything`).toBe(true);
    }
  });
});

describe("hierarchy", () => {
  it("every node reaches the root", () => {
    for (const node of NODES) {
      if (node.id === ROOT_ID) continue;
      const chain = ancestorsOf(node.id);
      expect(chain.length, `${node.id} has no ancestors`).toBeGreaterThan(0);
      expect(chain[chain.length - 1], `${node.id} does not reach the root`).toBe(ROOT_ID);
    }
  });

  it("has no parent cycles", () => {
    for (const node of NODES) {
      const chain = ancestorsOf(node.id);
      expect(new Set(chain).size, `cycle above ${node.id}`).toBe(chain.length);
    }
  });

  it("the first view is small enough to take in", () => {
    const topLevel = CHILDREN_BY_PARENT.get(ROOT_ID) ?? [];
    expect(topLevel.length).toBeGreaterThan(3);
    expect(topLevel.length).toBeLessThanOrEqual(9);
  });

  it("the determination engine expands into the parts the argument rests on", () => {
    // This is the click the whole demo is built around: the client's posting asks for
    // someone who understands the structure rather than someone who keys K-1 numbers,
    // and these children are the answer to that.
    const STAGE = "engine";
    const REQUIRED_CHILDREN = [
      "deterministic",
      "federal-rules",
      "protective",
      "state-rules",
      "crossborder-rules",
      "negative-findings",
      "authority",
      "llm-determination",
    ];

    expect(NODE_BY_ID.get(STAGE)?.parent).toBe(ROOT_ID);
    const children = (CHILDREN_BY_PARENT.get(STAGE) ?? []).map((n) => n.id);
    for (const child of REQUIRED_CHILDREN) {
      expect(children, `${STAGE} does not expand into ${child}`).toContain(child);
    }
  });

  it("the engine is the largest node on the graph", () => {
    // Size is a claim about importance. If another node outgrows the engine, the graph
    // is arguing for something the pitch is not.
    const engine = NODE_BY_ID.get("engine")!;
    for (const node of NODES) {
      if (node.id === "engine") continue;
      expect(node.size ?? 0, `${node.id} is drawn larger than the engine`).toBeLessThan(
        engine.size!,
      );
    }
  });

  it("anything not actually enabled says so", () => {
    const honest = NODES.some((n) =>
      /not enabled|opt-in|by default|deliberate/i.test(
        `${n.clientBenefit} ${n.userBenefit} ${n.metric?.value ?? ""}`,
      ),
    );
    expect(honest, "no node describes a deliberate limitation").toBe(true);
  });

  it("every estimated figure is flagged as estimated", () => {
    // One number a buyer checks and disproves discredits every other number on the page,
    // so projections must be visibly projections.
    for (const node of NODES) {
      if (!node.metric) continue;
      const soundsProjected = /projected|estimate|≈|~/i.test(
        `${node.metric.value} ${node.metric.caption}`,
      );
      if (soundsProjected) {
        expect(
          node.metric.estimated,
          `${node.id} reads as a projection but is not marked estimated`,
        ).toBe(true);
      }
    }
  });

  it("no two nodes share a client benefit", () => {
    // The self-check from the writing guide, made mechanical: if two clientBenefit lines
    // could be swapped without anyone noticing, they are filler.
    const benefits = NODES.map((n) => n.clientBenefit);
    expect(new Set(benefits).size).toBe(benefits.length);
  });
});

describe("the pipeline", () => {
  it("runs in the order an engagement travels", () => {
    expect(STAGES.map((s) => s.tier)).toEqual([
      "client",
      "ui",
      "gateway",
      "context",
      "engine",
      "data",
      "ops",
      "platform",
    ]);
  });

  it("gives every stage a distinct position on the flow axis", () => {
    const orders = STAGES.map((s) => s.flowOrder);
    expect(new Set(orders).size).toBe(orders.length);
  });

  it("only stages are pinned to the flow axis", () => {
    for (const node of NODES) {
      if (node.flowOrder === undefined) continue;
      expect(node.parent, `${node.id} is pinned but is not top level`).toBe(ROOT_ID);
    }
  });

  it("connects each stage to the next", () => {
    const stageOf = (nodeId: string): string | undefined => {
      for (const id of [nodeId, ...ancestorsOf(nodeId)]) {
        if (STAGES.some((s) => s.id === id)) return id;
      }
      return undefined;
    };

    const edges = new Set(
      LINKS.map((l) => {
        const s = stageOf(l.source);
        const t = stageOf(l.target);
        return s && t && s !== t ? `${s}->${t}` : null;
      }).filter(Boolean) as string[],
    );

    const REQUIRED_PATH = [
      "investor->workspace",
      "workspace->access",
      "access->factbase",
      "factbase->engine",
      "engine->record",
      "record->assurance",
      "assurance->platform",
    ];
    for (const step of REQUIRED_PATH) {
      expect(edges, `pipeline is broken at ${step}`).toContain(step);
    }
  });

  it("has a feedback edge flowing back upstream", () => {
    // Human corrections improving extraction is the only loop in the system, and it is
    // the reason review cost falls rather than stays flat.
    const order = new Map(STAGES.map((s, i) => [s.id, i]));
    const stageIndex = (nodeId: string): number | undefined => {
      for (const id of [nodeId, ...ancestorsOf(nodeId)]) {
        const position = order.get(id);
        if (position !== undefined) return position;
      }
      return undefined;
    };

    const backwards = LINKS.filter((l) => {
      const s = stageIndex(l.source);
      const t = stageIndex(l.target);
      return s !== undefined && t !== undefined && t < s;
    });
    expect(backwards.length, "no improvement loop in the graph").toBeGreaterThan(0);
  });

  it("every group summarises itself", () => {
    for (const [parentId] of CHILDREN_BY_PARENT) {
      if (parentId === ROOT_ID) continue;
      const parent = NODE_BY_ID.get(parentId);
      expect(parent, `${parentId} has children but is not a node`).toBeDefined();
      expect(parent!.clientBenefit.length).toBeGreaterThan(20);
      expect(parent!.userBenefit.length).toBeGreaterThan(20);
    }
  });

  it("every node answers all four questions substantially", () => {
    for (const node of NODES) {
      for (const field of ["what", "whyUsed", "clientBenefit", "userBenefit"] as const) {
        expect(node[field]?.length ?? 0, `${node.id}.${field} is thin`).toBeGreaterThan(40);
      }
      expect(node.demoNote.length, `${node.id} has no demo note`).toBeGreaterThan(20);
    }
  });

  it("the root is logical only — it has no node of its own", () => {
    expect(NODE_BY_ID.has(ROOT_ID)).toBe(false);
  });

  it("tree links match the parent fields exactly", () => {
    expect(TREE_LINKS.length).toBe(NODES.filter((n) => n.parent).length);
    for (const link of TREE_LINKS) {
      expect(NODE_BY_ID.get(link.target)?.parent).toBe(link.source);
    }
  });
});

describe("the mandated component chain is complete", () => {
  // By concept with a regex rather than by id, so a rename cannot silently drop a
  // required component. These are the pieces without which this is not a compliance
  // platform, only a document reader.
  const REQUIRED: [string, RegExp][] = [
    ["authentication", /authn|authentic/i],
    ["authorization", /authz|authoriz/i],
    ["firm tenancy", /tenanc|firm scop/i],
    ["K-1 extraction", /extract/i],
    ["human confirmation", /hitl|human confirm/i],
    ["the determination engine", /engine/i],
    ["authority citations", /authorit|citation/i],
    ["workpapers", /workpaper/i],
    ["the filing gate", /filing-gate|filing gate/i],
    ["open items", /open-items|open item/i],
    ["year-over-year tie-out", /tieout|tie-out/i],
    ["audit log", /audit/i],
    ["monitoring", /monitor|metric/i],
  ];

  it.each(REQUIRED)("includes %s", (_concept, pattern) => {
    const found = NODES.some((n) => pattern.test(n.id) || pattern.test(n.label));
    expect(found).toBe(true);
  });
});

describe("guided tour", () => {
  it("every stop points at a real node", () => {
    for (const stop of TOUR) {
      expect(NODE_BY_ID.has(stop.nodeId), `tour stop → ${stop.nodeId}`).toBe(true);
    }
  });

  it("has narration on every stop", () => {
    for (const stop of TOUR) {
      expect(stop.chapter.length).toBeGreaterThan(3);
      expect(stop.say.length).toBeGreaterThan(30);
    }
  });

  it("is long enough to carry the argument and short enough to record", () => {
    expect(TOUR.length).toBeGreaterThanOrEqual(15);
    expect(TOUR.length).toBeLessThanOrEqual(30);
  });

  it("covers the components that carry the commercial argument", () => {
    // A tour that skips these does not explain why the engagement is worth its fee.
    const REQUIRED = [
      "hitl",
      "engine",
      "deterministic",
      "protective",
      "state-rules",
      "crossborder-rules",
      "negative-findings",
      "llm-determination",
      "recon-1446",
      "filing-gate",
    ];

    const ids = TOUR.map((s) => s.nodeId);
    for (const required of REQUIRED) {
      expect(ids, `tour omits ${required}`).toContain(required);
    }
  });

  it("visits no node twice", () => {
    const ids = TOUR.map((s) => s.nodeId);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("starts with the client and ends on how it is run", () => {
    expect(NODE_BY_ID.get(TOUR[0]!.nodeId)?.tier).toBe("client");
    const lastTier = NODE_BY_ID.get(TOUR[TOUR.length - 1]!.nodeId)?.tier;
    expect(["ops", "platform"]).toContain(lastTier);
  });

  it("follows the pipeline in order", () => {
    const order = new Map(STAGES.map((s, i) => [s.id, i]));
    const stageOf = (nodeId: string): number | undefined => {
      for (const id of [nodeId, ...ancestorsOf(nodeId)]) {
        const position = order.get(id);
        if (position !== undefined) return position;
      }
      return undefined;
    };

    const positions = TOUR.map((stop) => stageOf(stop.nodeId)).filter(
      (p): p is number => p !== undefined,
    );
    for (let i = 1; i < positions.length; i++) {
      expect(
        positions[i]! >= positions[i - 1]!,
        `tour goes backwards at "${TOUR[i]!.chapter}"`,
      ).toBe(true);
    }
  });
});
