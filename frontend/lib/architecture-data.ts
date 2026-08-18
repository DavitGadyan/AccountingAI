/**
 * The architecture graph's content.
 *
 * Structured as the pipeline an engagement travels, in order: a pile of K-1 PDFs
 * arrives from five syndicators and a filed, cited, defensible set of U.S. returns
 * comes out the other end.
 *
 * Every node answers four questions — what it does, why it exists, what it saves the
 * firm, what the client feels — because a diagram of boxes explains nothing to the
 * person deciding whether to pay for it.
 *
 * Counts marked as measured are read from the code in this repository: 16 rules
 * registered for tax year 2025, 22 determinations produced against the reference
 * structure, 27 extracted fields per K-1, 7 profiled states, 61 backend tests. Legal
 * figures (penalties, rates, due dates) are statutory. Anything projected says so.
 *
 * Deliberately static. This page renders with the API stopped, so a demo can never
 * fail because a service is cold.
 */

import type { IconKey } from "@/lib/node-icons";

// ---------------------------------------------------------------------------
// Tiers — one per stage of the engagement. The determination engine carries the
// commercial argument, so it gets the one warm accent; everything else is muted.
// ---------------------------------------------------------------------------

export type TierId =
  | "client"
  | "ui"
  | "gateway"
  | "context"
  | "engine"
  | "data"
  | "ops"
  | "platform";

export interface Tier {
  id: TierId;
  label: string;
  blurb: string;
  color: string;
}

export const TIERS: Tier[] = [
  { id: "client", label: "People", blurb: "Investor, preparer, signer, syndicators", color: "#8d99a4" },
  { id: "ui", label: "Workspace", blurb: "Where the work is actually done", color: "#3f7a75" },
  { id: "gateway", label: "Access", blurb: "Tenancy, identity, who may sign", color: "#a9661b" },
  { id: "context", label: "Fact base", blurb: "Documents turned into reviewed facts", color: "#7a6ba8" },
  { id: "engine", label: "Determination", blurb: "Which forms, for which entity, and why", color: "#c8821f" },
  { id: "data", label: "Returns & record", blurb: "Prepared, filed, handed over", color: "#5b7596" },
  { id: "ops", label: "Assurance", blurb: "Gates, tie-outs, audit trail, deadlines", color: "#b04e72" },
  { id: "platform", label: "Platform", blurb: "How it runs and how it is proven", color: "#6b7280" },
];

// ---------------------------------------------------------------------------
// Nodes
// ---------------------------------------------------------------------------

export interface ArchNode {
  id: string;
  label: string;
  tier: TierId;
  /** Hierarchy. The graph opens collapsed and expands on click. */
  parent?: string;
  /** Position along the flow axis, top-level stages only. */
  flowOrder?: number;
  sub?: string;
  logo?: string;
  icon?: IconKey;
  size?: number;

  what: string;
  whyUsed: string;
  clientBenefit: string;
  userBenefit: string;
  metric?: { value: string; caption: string; estimated?: boolean };
  demoNote: string;
}

/** Logical parent only — deliberately has no node of its own. */
export const ROOT_ID = "root";

export const NODES: ArchNode[] = [
  // ==================================================== 0 · the people
  {
    id: "investor",
    label: "The investor",
    tier: "client",
    parent: ROOT_ID,
    flowOrder: 0,
    sub: "Canadian, 2 holdcos, 5 syndications",
    icon: "user",
    size: 8,
    what: "A Canadian investor holding passive LP interests in five U.S. multifamily syndications through two Ontario holding companies. Every spring, five K-1s arrive in five formats on five different schedules.",
    whyUsed:
      "This is the whole reason the system exists, and the reason it cannot be a generic tax product. The investor does not manage operating cash flow, does not know which of six states wants a return, and cannot tell from a K-1 whether Form 8865 applies to them. Somebody has to answer that every year, correctly, and be able to defend the answer.",
    clientBenefit:
      "A single fixed annual fee instead of an open-ended hourly engagement, and one advisor who owns the U.S. filing process end to end rather than a preparer who keys numbers and hands back a question.",
    userBenefit:
      "Spring stops being a season where they chase five syndicators and hope their accountant asks the right questions. They upload documents as they arrive and are told what is still missing.",
    metric: { value: "5 + 2", caption: "syndications and Canadian holding companies in the reference structure" },
    demoNote:
      "Start here, not at the technology. Everything downstream earns its place by answering one question: which U.S. returns does this person owe, and can we prove why.",
  },
  {
    id: "syndicators",
    label: "The syndicators",
    tier: "client",
    parent: "investor",
    sub: "5 issuers · K-1, K-3, 8805",
    icon: "layers",
    size: 5,
    what: "The five sponsors who issue the K-1s, K-3s and Forms 8805. They are not users of the system, but almost every delay and every defect in an engagement originates with them.",
    whyUsed:
      "Without modelling them explicitly, the platform cannot tell 'a K-1 has not arrived' from 'this investment was exited' — and those two facts lead to opposite conclusions. One means chase the sponsor; the other means run a §731 disposition analysis.",
    clientBenefit:
      "Expected-versus-received is computed per partnership, so the chase list is generated rather than remembered. A K-3 that never arrives is an open item in March instead of an amended return in November — and an amended 1120-F is a re-run of the entire engagement at zero additional fee.",
    userBenefit:
      "The investor is asked for exactly the documents that are actually missing, once, with the sponsor named — not a generic annual checklist.",
    demoNote:
      "Late and amended K-1s are the single biggest driver of cost in this work. The system is built around that fact rather than in spite of it.",
  },
  {
    id: "preparer",
    label: "Preparer",
    tier: "client",
    parent: "investor",
    sub: "works the queue",
    icon: "assistant",
    size: 5,
    what: "The staff accountant who reviews extractions, resolves open items and assembles the returns. They can do everything in the system except approve and transmit.",
    whyUsed:
      "The economics of a fixed fee are entirely preparer hours. If review costs more than manual entry, the automation is a net loss and the engagement stops being profitable at any fee the client will accept.",
    clientBenefit:
      "Estimated 12 preparer hours down to roughly 3 in a recurring year. Against the posted $1,000 fixed fee, that is the difference between a loss-making engagement and a repeatable one.",
    userBenefit:
      "Their day is confirming numbers next to the page they came from, not retyping forty boxes and hoping they did not transpose one.",
    metric: { value: "12h → ~3h", caption: "preparer hours per recurring year — projected, not yet measured", estimated: true },
    demoNote:
      "That hours figure is a projection and the node says so. Overstate one number a buyer checks and every other number on this page stops counting.",
  },
  {
    id: "signer",
    label: "Signer — CPA / EA",
    tier: "client",
    parent: "investor",
    sub: "the only role that can file",
    icon: "shield",
    size: 6,
    what: "The credentialed reviewer who approves determinations, signs returns and authorises transmission. Their credential is a stored field, not a job title in a directory.",
    whyUsed:
      "Circular 230 requires a credentialed signer, and 'we have a policy' is not a control. Without an enforced role, an automated pipeline will eventually file something nobody read, and the first time anyone finds out is a notice.",
    clientBenefit:
      "There is no code path that transmits a return without a recorded approval event against a credentialed user id. Not a setting, not a feature flag — the path does not exist, which is a materially different statement to a firm's professional-liability carrier.",
    userBenefit:
      "The investor knows a named professional read the return. The name and credential number are in the filing record they receive.",
    demoNote:
      "Say this plainly: the machine decides nothing that gets filed. It decides what to propose, and a human with a licence decides what goes.",
  },

  // ==================================================== 1 · workspace
  {
    id: "workspace",
    label: "Workspace",
    tier: "ui",
    parent: ROOT_ID,
    flowOrder: 1,
    sub: "Next.js 15 · App Router · React 19",
    logo: "nextjs",
    icon: "browser",
    size: 9,
    what: "The application the firm works in: engagement dashboard, extraction review, determination list with citations, workpapers, open items and the filing screen.",
    whyUsed:
      "Tax software optimises for keying a return. This work is not keying — it is deciding, checking and evidencing. A UI built around a form layout makes the deciding invisible, which is exactly the part the client is paying for.",
    clientBenefit:
      "Every screen is organised around a decision that has to be made rather than a form that has to be filled. The determination list shows the authority for each conclusion inline, so a reviewer checks a position without leaving the page or opening a code section.",
    userBenefit:
      "A preparer can see, in one glance at the overview, what is blocking the engagement and what deadline is closest. Nothing is buried three menus deep.",
    demoNote:
      "Six tabs, and each maps to one of the ten numbered items in the client's own scope of work. That mapping was deliberate.",
  },
  {
    id: "review-queue",
    label: "Extraction review",
    tier: "ui",
    parent: "workspace",
    sub: "value · confidence · page · source line",
    icon: "compare",
    size: 6,
    what: "The queue where a human confirms or corrects every extracted number that the model was not confident about, with the page number and the source line shown next to it.",
    whyUsed:
      "Review without provenance is not review — it is re-entry. If checking a figure means opening a forty-page PDF and hunting, the preparer will start trusting the model instead, and that is the failure mode that ends up on a filed return.",
    clientBenefit:
      "Provenance turns a per-field check into about two seconds. At 27 extracted fields per K-1 and five K-1s, that is the difference between review being cheaper than manual entry and being more expensive than it.",
    userBenefit:
      "The number, the confidence, the page and the line it came from sit on one row. Confirm, or type the right value and move on.",
    metric: { value: "27 fields", caption: "extracted per K-1 — measured from the extraction schema in this repo" },
    demoNote:
      "The schema is deliberately 27 fields, not 200. A short schema extracts more accurately than an exhaustive one, and the boxes we skip are boxes this engagement does not use.",
  },
  {
    id: "structure-map",
    label: "Structure map",
    tier: "ui",
    parent: "workspace",
    sub: "tiered ownership diagram",
    icon: "cluster",
    size: 5,
    what: "The ownership graph — Canadian holdcos above U.S. limited partnerships — with each partnership's property states on the node.",
    whyUsed:
      "Filing obligations follow the shape of the structure. Get one ownership edge wrong and every determination beneath it is wrong, silently, in a way no downstream check will catch.",
    clientBenefit:
      "The structure is confirmed once, visually, in year one. Year two re-runs against the same graph — which is why a recurring year is a re-run rather than a rebuild, and why the recurring fee can be lower than the first-year fee.",
    userBenefit:
      "The investor can look at one picture and confirm it matches what they actually own. Most of them have never seen their own structure drawn.",
    demoNote:
      "This one is drawn as a tiered diagram, not a force graph, because ownership has a direction. The 3D treatment you are looking at now is for the system, not for the tax structure — they want opposite handling.",
  },
  {
    id: "client-portal",
    label: "Client portal",
    tier: "ui",
    parent: "workspace",
    sub: "upload · status · deliverables",
    icon: "archive",
    size: 5,
    what: "The investor's own view: upload documents as they arrive, see what is still outstanding, and collect the final package.",
    whyUsed:
      "Documents arriving as email attachments across four months is how versions get confused and how an amended K-1 ends up sitting beside the original instead of replacing it.",
    clientBenefit:
      "Every document lands in the engagement with a content hash and a timestamp. The same PDF sent three times by a sponsor is stored and extracted once, which removes an entire category of double-counting.",
    userBenefit:
      "The investor stops wondering whether their accountant received something. The status is on the screen.",
    demoNote:
      "Scope item 9 is 'provide a completed copy of all filed returns'. This is where that lands, and it is generated, not assembled by hand.",
  },

  // ==================================================== 2 · access
  {
    id: "access",
    label: "Access control",
    tier: "gateway",
    parent: ROOT_ID,
    flowOrder: 2,
    sub: "FastAPI dependencies",
    logo: "fastapi",
    icon: "gateway",
    size: 9,
    what: "Identity, role and firm scoping, enforced as request dependencies on every route that touches client data.",
    whyUsed:
      "A tax platform holds EINs, TINs, capital accounts and prior-year returns for multiple firms. One cross-tenant read is not a bug report, it is a breach notification and a professional-conduct problem for every firm on the system.",
    clientBenefit:
      "Tenancy is a route dependency rather than a WHERE clause a developer remembers to add. A missing firm filter fails at the type of the handler, not in production.",
    userBenefit:
      "Nothing the user notices, which is the correct outcome for this layer.",
    demoNote:
      "Three checks, applied in order, on every request. The interesting one is the third.",
  },
  {
    id: "authn",
    label: "Authentication",
    tier: "gateway",
    parent: "access",
    sub: "JWT · bcrypt",
    icon: "key",
    size: 5,
    what: "Verifies who is making the request and rejects inactive users.",
    whyUsed:
      "Without it every other control is decorative. It also has to fail identically for an unknown email and a wrong password — anything else is a user-enumeration oracle against a list of accounting firms.",
    clientBenefit:
      "Login failures return one message for both cases, so the endpoint cannot be used to discover which firms are customers. That is a small detail that costs nothing to get right and cannot be retrofitted after a scrape.",
    userBenefit:
      "One sign-in, eight-hour session, no re-authentication in the middle of reviewing a K-1.",
    demoNote:
      "Same error message whether the email is unknown or the password is wrong. Deliberate.",
  },
  {
    id: "authz",
    label: "Authorization",
    tier: "gateway",
    parent: "access",
    sub: "role gates · reviewer-only actions",
    icon: "shield",
    size: 6,
    what: "Decides what this user may do. Approving a return, transmitting it, waiving a blocking open item and overriding a determination are reviewer-only actions.",
    whyUsed:
      "The dangerous actions in this system are not deletes — they are approvals. A preparer who can waive a blocking item can file a return with a missing K-3, and the system would look like it worked.",
    clientBenefit:
      "The four irreversible actions are gated to a credentialed role server-side. Hiding a button is not a control; the API refuses regardless of what the UI shows.",
    userBenefit:
      "A preparer is never in the position of accidentally doing something only a signer should do.",
    demoNote:
      "Note which actions are reviewer-only. They are exactly the ones that are hard to walk back.",
  },
  {
    id: "tenancy",
    label: "Firm scoping",
    tier: "gateway",
    parent: "access",
    sub: "firm_id on every table",
    icon: "layers",
    size: 5,
    what: "Every row in every table carries the firm that owns it, and every query filters on the firm id derived from the token — never from the request body.",
    whyUsed:
      "Taking the tenant id from the request is the single most common way multi-tenant systems leak. It looks correct in code review because the parameter is right there.",
    clientBenefit:
      "A request for another firm's engagement returns exactly the same 404 as one for a record that does not exist. The distinction between 'not found' and 'not yours' is itself a leak, so the API refuses to make it.",
    userBenefit:
      "Firms sharing the platform never see each other, including in error messages.",
    demoNote:
      "Identical 404 for 'does not exist' and 'belongs to someone else'. That is a deliberate choice, and it is in the code with a comment saying why.",
  },

  // ==================================================== 3 · fact base
  {
    id: "factbase",
    label: "Fact base",
    tier: "context",
    parent: ROOT_ID,
    flowOrder: 3,
    sub: "documents → reviewed facts",
    icon: "ledgerbook",
    size: 10,
    what: "Everything that turns a folder of PDFs into a typed, reviewed set of facts: intake, classification, extraction, human confirmation, the entity graph and last year's carryforwards.",
    whyUsed:
      "The determination engine is only as good as what it reads. Feeding it unreviewed model output would make every downstream citation a citation of a guess, which is worse than having no engine at all because it looks authoritative.",
    clientBenefit:
      "One rule governs this whole stage: nothing reaches a return without passing through a reviewed state. That single constraint is what lets the firm put its name on the output of an automated pipeline.",
    userBenefit:
      "The investor uploads documents in whatever order the sponsors send them and the system sorts out what each one is.",
    demoNote:
      "This is the boundary between what a model produces and what a professional signs. Everything on the left is a proposal; everything on the right is evidence.",
  },
  {
    id: "intake",
    label: "Intake & dedupe",
    tier: "context",
    parent: "factbase",
    sub: "SHA-256 content addressing",
    icon: "archive",
    size: 5,
    what: "Accepts uploads, hashes the contents, and refuses a file already present in the engagement.",
    whyUsed:
      "Sponsors re-send the same K-1 constantly — a portal copy, an email copy, a copy attached to the year-end statement. Extracting each one produces three sets of review rows for one document and a real risk of counting an amount twice.",
    clientBenefit:
      "Duplicate uploads cost nothing: no second extraction, no second review queue, no duplicated K-1 in the fact base. The check is one indexed lookup on the upload path.",
    userBenefit:
      "The investor can forward everything without worrying about sending something twice.",
    demoNote:
      "Content hash, not filename. Sponsors rename files constantly and the bytes are what matter.",
  },
  {
    id: "classifier",
    label: "Classification",
    tier: "context",
    parent: "factbase",
    sub: "Claude · what is this document",
    logo: "anthropic",
    icon: "brain",
    size: 5,
    what: "Identifies what an unlabelled PDF actually is — a 2025 K-3 Part IV from a named fund, a prior-year 1120-F, an 8805, a capital account statement.",
    whyUsed:
      "Nobody wants to hand-label forty PDFs a year, and mis-filing a document is worse than not having it: a K-3 filed as 'other' is a K-3 the completeness check will report as missing.",
    clientBenefit:
      "Zero manual filing of documents into categories. Where the year is not printed on the page the model returns null rather than inferring it — a wrong year silently files a document against the wrong engagement, which is the one error nothing downstream would catch.",
    userBenefit:
      "The investor forwards whatever the sponsors send, in whatever order it arrives, and never has to work out what any of it is called before uploading it.",
    demoNote:
      "The prompt explicitly forbids inferring the tax year from context. Null is a better answer than a plausible wrong one.",
  },
  {
    id: "extractor",
    label: "K-1 / K-3 extraction",
    tier: "context",
    parent: "factbase",
    sub: "27 typed fields · per-field confidence",
    logo: "anthropic",
    icon: "chip",
    size: 7,
    what: "Pulls the K-1 boxes, capital account rollforward, liability detail and K-3 source data into a typed schema, with a confidence, a page number and the source line for every value.",
    whyUsed:
      "This is the part that is genuinely tedious and genuinely mechanical. It is also the part where a model is at its most useful and least dangerous, because every output is checkable against a page reference in seconds.",
    clientBenefit:
      "Estimated well under a dollar of model spend per K-1 against roughly 20 minutes of keying. The prompt encodes the two rules a junior always gets wrong: parentheses mean negative, and a blank box is null, never zero.",
    userBenefit:
      "Nothing directly — but the reason the preparer's day is confirmations rather than keying starts here.",
    metric: { value: "≈ $0.30 / K-1", caption: "model spend per document — projected from token counts, not yet measured", estimated: true },
    demoNote:
      "Blank is not zero. Zero is an assertion that the partnership reported nothing; blank is an absence, and those two lead to different determinations downstream.",
  },
  {
    id: "hitl",
    label: "Human confirmation",
    tier: "context",
    parent: "factbase",
    sub: "threshold 0.90 · corrections stored",
    icon: "thumb",
    size: 7,
    what: "Anything the model scored below 0.90 goes to a person. The human's value is stored alongside the model's original rather than replacing it.",
    whyUsed:
      "A confidence score that does not change what happens is decoration. This is the switch that makes it mean something — and keeping both values is what turns every correction into evidence of whether extraction quality is drifting.",
    clientBenefit:
      "Keeping the pair costs one column and gives the firm a measured auto-accept rate per prompt version. Without it, nobody can answer 'is this getting better or worse' except by feel, and 'by feel' is how a quiet regression survives a whole filing season.",
    userBenefit:
      "The investor's return rests on numbers a person looked at. Not most of them — all of the uncertain ones.",
    metric: { value: "0.90", caption: "confidence floor; below it a field cannot reach a return without a human" },
    demoNote:
      "The threshold is a config value with a comment explaining the trade-off. Set it too high and review costs more than typing; too low and a wrong number reaches a filed return.",
  },
  {
    id: "entity-graph",
    label: "Entity & ownership graph",
    tier: "context",
    parent: "factbase",
    sub: "profits % · capital % · property situs",
    icon: "cluster",
    size: 6,
    what: "The structure as data: entities, directed ownership edges with separate profits and capital percentages, treaty posture, and the states each partnership's property sits in.",
    whyUsed:
      "Profits and capital diverge sharply in a syndication waterfall and they drive different rules. Collapsing them into one 'ownership %' is the kind of simplification that produces a confidently wrong answer.",
    clientBenefit:
      "State nexus is computed from where the buildings are, not where the partnership was formed. A Delaware LP owning a Georgia apartment complex creates a Georgia obligation and no Delaware one — an engine keyed on formation state gets that exactly backwards.",
    userBenefit:
      "The investor is asked about their structure once. After that it is data, and it carries into every future year.",
    demoNote:
      "Two percentages, not one, and the property situs on the partnership rather than on the holdco. Both of those are load-bearing.",
  },
  {
    id: "carryforward",
    label: "Prior-year carryforward",
    tier: "context",
    parent: "factbase",
    sub: "basis · at-risk · PAL · EBIE",
    icon: "loop",
    size: 6,
    what: "Reads last year's return and workpapers for the balances that persist: outside basis, at-risk amount, suspended passive losses, §163(j) excess business interest, and any elections already on file.",
    whyUsed:
      "These balances are the memory of the investment. Restarting them at zero each year is how a suspended loss quietly disappears and how a §882(d) election that binds all future years gets made twice.",
    clientBenefit:
      "Scope item 1 — review the prior-year returns and existing structure — is a one-time ingest rather than an annual re-read. EBIE is tracked per partnership and never pooled, because it releases only against excess taxable income from the same partnership.",
    userBenefit:
      "Losses the investor could not use this year are still there next year, and they can see the balance rather than trusting that someone carried it.",
    demoNote:
      "EBIE is per-partnership. Pool it across the five syndications and the number is wrong every year afterwards, compounding.",
  },

  // ==================================================== 4 · determination engine
  {
    id: "engine",
    label: "Determination engine",
    tier: "engine",
    parent: ROOT_ID,
    flowOrder: 4,
    sub: "16 rules · versioned by tax year",
    icon: "brain",
    size: 12,
    what: "Runs every registered rule for the tax year against the fact base and produces a per-entity form matrix: which returns are required, which are protective, which are not required and why.",
    whyUsed:
      "This is the sentence in the client's own posting: 'someone who understands the underlying tax structure, not someone who simply enters numbers from K-1s into tax software.' Determination is the work. Everything else in this system is logistics around it.",
    clientBenefit:
      "16 rules produce 22 determinations against the reference structure — every one carrying its statutory authority and the facts that triggered it. The firm's judgement is encoded once and applied identically in year one and year six, which is what makes a fixed recurring fee safe to quote.",
    userBenefit:
      "The investor gets an answer with a reason attached, in a paragraph they can read, rather than a form they have to trust.",
    metric: { value: "16 → 22", caption: "rules registered for TY2025, determinations produced — measured in this repo" },
    demoNote:
      "Open this one. The single most important decision in the system is what it is written in, and it is not what most people assume.",
  },
  {
    id: "deterministic",
    label: "Deterministic, not inferred",
    tier: "engine",
    parent: "engine",
    sub: "pure Python · no model call",
    icon: "chip",
    size: 8,
    what: "Every filing determination is ordinary Python. There is no model in this path, and rules may not read each other's output.",
    whyUsed:
      "A tax position has to be reproducible. The same facts must yield the same forms in 2031 as in 2026, and a difference between two years must be explainable by a change in facts — not by a change in model weights, a temperature setting, or a vendor's silent upgrade.",
    clientBenefit:
      "Re-running a prior year reproduces that year's answer exactly, which is what makes an examination survivable. A firm that cannot reproduce its own prior-year conclusion is negotiating from nothing.",
    userBenefit:
      "The investor's 2026 return will not disagree with their 2025 return for reasons nobody can explain.",
    metric: { value: "3 years", caption: "rule sets registered side by side — 2024, 2025, 2026" },
    demoNote:
      "This is the architectural claim worth defending. The model reads documents; it does not decide filing positions. Those are different jobs and only one of them tolerates non-determinism.",
  },
  {
    id: "federal-rules",
    label: "Federal rules",
    tier: "engine",
    parent: "engine",
    sub: "1120-F · 8805 · 8833 · 5472 · 8990",
    icon: "ledger",
    size: 7,
    what: "The U.S. federal rule set: ECI and Form 1120-F, protective returns, branch profits tax, treaty disclosure, §1446 withholding credits, FIRPTA, §163(j), and the loss limitation stack.",
    whyUsed:
      "A Canadian corporation holding an LP interest in a partnership that owns U.S. real property has effectively connected income under §875(1) and §897(a). That conclusion drives everything else, and it is not obvious from reading a K-1.",
    clientBenefit:
      "The loss limitation stack runs in statutory order — §704(d), then §465, then §469, then §461(l). Applying §469 first puts the suspended loss in the wrong bucket with the wrong release condition, and that error compounds for the entire life of the investment.",
    userBenefit:
      "Losses that are suspended are suspended for a stated reason, and the investor is told which future event releases them.",
    demoNote:
      "Order matters here in a way that most software gets wrong. The tests assert the order, not just the outcome.",
  },
  {
    id: "protective",
    label: "Protective return logic",
    tier: "engine",
    parent: "engine",
    sub: "Reg. §1.882-4(a)(3)(vi)",
    icon: "shield",
    size: 7,
    what: "When a holdco has a U.S. partnership interest but no effectively connected income this year, the engine still calls for a protective Form 1120-F rather than concluding nothing is due.",
    whyUsed:
      "Filing nothing is the intuitive answer and it is the expensive one. Without a timely return, §882(c)(2) denies the foreign corporation all deductions and credits — it is then taxed on gross ECI, not net, in any year the position is later challenged.",
    clientBenefit:
      "A protective return costs a few hundred dollars in preparation. Losing every deduction against gross rental income on a multifamily portfolio costs a multiple of the investment's annual income. This one rule can outweigh the entire annual fee.",
    userBenefit:
      "The investor is protected against a downside they would never have known to ask about.",
    demoNote:
      "This is the clearest example of why 'no income, no filing' is the wrong instinct. It is also the kind of thing a form-filling preparer never raises.",
  },
  {
    id: "state-rules",
    label: "State nexus rules",
    tier: "engine",
    parent: "engine",
    sub: "7 states profiled · situs-driven",
    icon: "layers",
    size: 6,
    what: "Determines state obligations from where the property sits, with a profiled rule per state and an explicit needs-research flag for anything outside the profile.",
    whyUsed:
      "The recurring failure in this work is not getting a state wrong. It is never looking at a state at all — Tennessee franchise and excise tax reaches limited partnerships directly and is the most commonly missed filing in a multifamily portfolio.",
    clientBenefit:
      "Texas is examined despite having no income tax, because it has a margin tax with an entity-level nexus test. States concluded not to require a return are recorded with the threshold that was tested, so next year is a comparison rather than a re-derivation.",
    userBenefit:
      "The investor is not surprised three years later by a state they have never heard from.",
    metric: { value: "7 states", caption: "TX, GA, FL, NC, AZ, TN, OH — where multifamily syndications concentrate" },
    demoNote:
      "Note that a state can be examined and produce a documented 'no return due'. A negative conclusion with a threshold attached is a deliverable, not an omission.",
  },
  {
    id: "composite-choice",
    label: "Composite vs. separate",
    tier: "engine",
    parent: "engine",
    sub: "both outcomes computed",
    icon: "compare",
    size: 6,
    what: "When a sponsor has made a composite state election, the engine computes the partner's position both ways instead of accepting the sponsor's default.",
    whyUsed:
      "A composite filing usually relieves the partner of a separate return — and sometimes leaves them worse off, because it applies the top marginal rate with no exemptions and no ability to use other-activity losses or state credits.",
    clientBenefit:
      "The choice is surfaced as a decision with both numbers attached. The sponsor made that election for the sponsor's convenience, and nobody asked whether it suited this investor.",
    userBenefit:
      "A decision the investor did not know existed gets made in their favour, with the arithmetic shown.",
    demoNote:
      "The syndicator made this election without asking. That is normal, and it is exactly the sort of thing a fixed-fee annual reviewer should be catching.",
  },
  {
    id: "crossborder-rules",
    label: "Cross-border & treaty",
    tier: "engine",
    parent: "engine",
    sub: "Art. X(6) · XXIX-A LOB · 8833",
    icon: "gateway",
    size: 7,
    what: "The Canada–U.S. treaty layer: branch profits at the reduced rate, the limitation-on-benefits analysis it depends on, Form 8833 disclosure, and advisory flags for the Canadian side.",
    whyUsed:
      "Article X(6) cuts branch profits tax from 30% to 5% — but only for a qualifying person under Article XXIX-A. Claiming the rate without recording that analysis is a position with nothing behind it, and it is the largest single number on the return.",
    clientBenefit:
      "The engine refuses to claim the 5% rate until the LOB analysis is documented against the entity; until then it returns needs-analysis with reduced confidence rather than a number. Undisclosed treaty positions also carry a $1,000 penalty per failure under §6712.",
    userBenefit:
      "The investor's treaty benefits are claimed on a basis that holds up, rather than assumed because everyone assumes it.",
    metric: { value: "30% → 5%", caption: "branch profits rate under Canada–U.S. Treaty Art. X(6), subject to LOB" },
    demoNote:
      "Watch what happens when the LOB analysis is missing. It does not guess and it does not claim — it stops and asks.",
  },
  {
    id: "negative-findings",
    label: "Documented negatives",
    tier: "engine",
    parent: "engine",
    sub: "the Form 8865 answer",
    icon: "ledger",
    size: 7,
    what: "Conclusions of 'not required' are stored and reported with their reasoning, not silently omitted.",
    whyUsed:
      "The client asked about Form 8865 by name. Silence is not an answer to that question — and a year later nobody can tell whether it was considered and rejected, or never considered.",
    clientBenefit:
      "The engine records that 8865 is the mirror image of this structure: it applies to a U.S. person holding a foreign partnership interest, whereas here a Canadian corporation holds U.S. LPs, so no §6038 obligation arises. Four such documented negatives are produced against the reference structure, and they are what make next year's review a comparison.",
    userBenefit:
      "The investor gets an explicit written answer to the question they actually asked, including where the answer is 'no'.",
    demoNote:
      "This is the one that wins the engagement. The client asked about 8865 specifically. Most applicants will either ignore it or file one unnecessarily.",
  },
  {
    id: "authority",
    label: "Authority citations",
    tier: "engine",
    parent: "engine",
    sub: "IRC § · Treas. Reg. · treaty article",
    icon: "ledger",
    size: 7,
    what: "Every determination carries the statute, regulation, treaty article or form instruction it rests on, and that citation flows through to the workpaper and the client memo.",
    whyUsed:
      "A determination you cannot cite is a determination you cannot defend. Under examination, 'the software said so' is not a position.",
    clientBenefit:
      "The workpaper file is examination-ready as a by-product of doing the work, rather than as a separate reconstruction exercise months later when the person who did it has left.",
    userBenefit:
      "The investor can hand any conclusion to a second opinion and have it checked in minutes.",
    demoNote:
      "Click any determination in the app and the authority is right there. Nothing had to be written twice for that to be true.",
  },
  {
    id: "override",
    label: "Reviewer override",
    tier: "engine",
    parent: "engine",
    sub: "reason required · survives re-runs",
    icon: "thumb",
    size: 6,
    what: "A reviewer may disagree with the engine, but only with a written reason. The override survives every subsequent re-run and appears in the client memo.",
    whyUsed:
      "An engine nobody can override is an engine nobody trusts. An override nobody can see is worse — it hides a professional judgement in a database field.",
    clientBenefit:
      "Re-running the determination never silently discards a human decision: overrides and resolved open items are preserved while computed output is replaced. Without that, re-running becomes something staff avoid, and stale determinations get filed.",
    userBenefit:
      "Where a professional overruled the system, the investor is told, and told why.",
    demoNote:
      "Overrides are tracked as a metric and deliberately not minimised. A reviewer who never overrides is a reviewer who is not reading.",
  },
  {
    id: "llm-determination",
    label: "Model-decided positions",
    tier: "engine",
    parent: "engine",
    sub: "built · deliberately not enabled",
    icon: "scissors",
    size: 7,
    what: "The infrastructure to let a model decide filing requirements directly from documents exists — the extraction client, the schemas and the prompts are all in place. It is not wired into the determination path.",
    whyUsed:
      "It would demo beautifully and it would be genuinely faster to build than 16 hand-written rules with citations.",
    clientBenefit:
      "Not enabled by default, and this is deliberate. A model-decided position cannot be reproduced across years, cannot carry a citation it did not invent, and cannot be defended on examination by anyone. On a $1,000 fixed-fee engagement, one wrong §882(c)(2) conclusion costs more than the entire annual fee, and the failure mode is silent: the output looks exactly as authoritative when it is wrong.",
    userBenefit:
      "Nothing changes for the investor, which is the point — their filing positions do not vary with a vendor's model release.",
    demoNote:
      "Say this one out loud. We could have shipped an LLM that picks the forms. We deliberately did not, and the reason is that the failure mode is invisible.",
  },

  // ==================================================== 5 · returns & record
  {
    id: "record",
    label: "Returns & record",
    tier: "data",
    parent: ROOT_ID,
    flowOrder: 5,
    sub: "PostgreSQL · workpapers · e-file",
    logo: "postgres",
    icon: "database",
    size: 9,
    what: "Where determinations become returns: generated workpapers, form assembly, transmission through an authorised e-file provider, and the client deliverable package.",
    whyUsed:
      "The determination is worthless until it is filed and until the client has a copy of what was filed with the schedules behind it.",
    clientBenefit:
      "Scope items 4, 5, 9 and the deliverables list — filed returns, confirmations, workpapers, summary memo — are produced by the pipeline rather than assembled by hand at the end of the engagement.",
    userBenefit:
      "One package, indexed, at the end. Not a series of emails with attachments named final_v3.",
    demoNote:
      "Everything in this stage is regenerable from the fact base. Nothing here is hand-keyed, which is why year two is cheap.",
  },
  {
    id: "workpapers",
    label: "Workpaper generation",
    tier: "data",
    parent: "record",
    sub: "7 schedules · regenerated per run",
    icon: "ledger",
    size: 6,
    what: "Generates the supporting schedules: K-1 summary, §1446 reconciliation, the loss limitation stack, the state matrix, and a determination index listing every rule evaluated.",
    whyUsed:
      "Workpapers are the difference between a return and a defensible return. Hand-built ones are also the reason year two costs nearly as much as year one at most firms.",
    clientBenefit:
      "7 schedules generated per run against the reference structure, each reproducible from the fact base at any time. The determination index doubles as an assurance list: all 16 rules, with their conclusions, on one page.",
    userBenefit:
      "The investor receives the arithmetic, not just the answer, and the narrative next to each schedule is in plain English.",
    metric: { value: "7 schedules", caption: "generated for the reference structure — measured in this repo" },
    demoNote:
      "The §1446 reconciliation is the one that earns its place. It catches the defect that actually happens.",
  },
  {
    id: "recon-1446",
    label: "§1446 reconciliation",
    tier: "data",
    parent: "record",
    sub: "8805 payee vs. filer TIN",
    icon: "compare",
    size: 6,
    what: "Ties each Form 8805 to the corresponding K-1 box 15 code O and checks that the payee TIN is actually the filing entity's.",
    whyUsed:
      "Sponsors routinely withhold at the right rate and issue the 8805 to the wrong tier of the structure. If the payee TIN is not the filer's, the credit is at risk — and only the partnership can fix it, which takes weeks.",
    clientBenefit:
      "A mismatch is caught before filing rather than by an IRS notice disallowing the credit. At the 21% corporate withholding rate on a mid-six-figure ECTI allocation, a disallowed credit is a five-figure cash item plus an amended return.",
    userBenefit:
      "Tax the investor already paid actually gets credited, in the year it belongs to.",
    metric: { value: "21%", caption: "§1446 withholding rate on ECTI allocable to a corporate foreign partner" },
    demoNote:
      "This is the most valuable check in the system per line of code. It is also the sort of thing only someone who has done this work knows to build.",
  },
  {
    id: "efile",
    label: "E-file transmission",
    tier: "data",
    parent: "record",
    sub: "MeF adapter · stub for CI",
    icon: "gateway",
    size: 6,
    what: "An adapter over an IRS-authorised transmitter: submit, poll for acknowledgement, record the submission id and reject codes.",
    whyUsed:
      "Becoming an authorised transmitter is a business, not a feature. Pretending otherwise adds years of compliance work to a product that should integrate with one.",
    clientBenefit:
      "The interface is deliberately thin — authenticate, submit, poll — with a stub implementation used in development and CI. Switching providers is one class, not a migration, and no test in the suite can accidentally reach the IRS.",
    userBenefit:
      "Filing confirmations arrive as a record in the package rather than as a screenshot.",
    demoNote:
      "Note the stub. Every test in this repo runs with no network and no chance of transmitting anything real.",
  },
  {
    id: "deliverable",
    label: "Client package & memo",
    tier: "data",
    parent: "record",
    sub: "returns · confirmations · plain-English memo",
    icon: "archive",
    size: 6,
    what: "Assembles the filed returns, filing confirmations, workpapers and a written summary of the material tax issues for the following year.",
    whyUsed:
      "The last item on the client's deliverables list is 'a brief summary of any material tax issues I should be aware of'. That is the part a form-filling preparer never produces, and it is the part that makes the relationship annual.",
    clientBenefit:
      "The memo is generated deterministically from the determinations and variances — including the Canadian-side items this engagement does not file — so it exists even with no model reachable. A deliverable that depends on an API being up is a deliverable that fails on the day it is needed.",
    userBenefit:
      "The investor reads six paragraphs and understands their own tax position, including what to hand to their Canadian accountant.",
    demoNote:
      "The memo names T1134, T1135 and the foreign tax credit timing mismatch. None of those are filed here — flagging them is the difference between a preparer and an advisor.",
  },

  // ==================================================== 6 · assurance
  {
    id: "assurance",
    label: "Assurance",
    tier: "ops",
    parent: ROOT_ID,
    flowOrder: 6,
    sub: "gates · tie-outs · audit · deadlines",
    icon: "chart",
    size: 9,
    what: "Everything that decides whether the work is finished and proves what happened: the filing gate, open items, year-over-year tie-out, the audit log and deadline tracking.",
    whyUsed:
      "In tax work the risk is not that the system goes down. It is that it produces something plausible and wrong, and nobody notices until a notice arrives eighteen months later.",
    clientBenefit:
      "Four independent checks stand between a prepared return and a transmitted one, and each is enforced server-side at the moment of transmission rather than at approval time.",
    userBenefit:
      "The investor's return does not get filed with a known gap in it.",
    demoNote:
      "This stage is why the firm can put a fixed fee on the engagement without carrying open-ended risk.",
  },
  {
    id: "filing-gate",
    label: "Filing gate",
    tier: "ops",
    parent: "assurance",
    sub: "no override flag exists",
    icon: "shield",
    size: 8,
    what: "Four conditions checked before any transmission: the return is approved, the approver is a reviewer, the approver holds a credential, and no blocking open item is outstanding.",
    whyUsed:
      "Checks that live inside a route handler get bypassed by the second code path someone adds. This is a separate object with a single assert method, and every transmission path in the codebase calls it.",
    clientBenefit:
      "There is no override parameter and no force flag — deliberately. Conditions are re-checked at transmission, not trusted from approval, because an open item can be reopened in between. All failures are reported at once rather than one per attempt.",
    userBenefit:
      "Nothing incomplete gets filed in the investor's name.",
    demoNote:
      "Try to transmit with a blocking item open. It refuses, lists every reason at once, and there is no way to insist.",
  },
  {
    id: "open-items",
    label: "Open items",
    tier: "ops",
    parent: "assurance",
    sub: "missing K-3 · no EIN · LOB undocumented",
    icon: "compare",
    size: 6,
    what: "Detects what is missing before filing: unreceived K-1s and K-3s, missing U.S. TINs, undocumented treaty positions and unestablished opening basis.",
    whyUsed:
      "Scope item 8 is 'identify any missing information before filing'. A missing K-3 found in March costs an email; found in November it costs an amended return.",
    clientBenefit:
      "Detection runs on every pipeline pass rather than once at the end, and blocking items are wired to the filing gate. A resolved item requires a written note — an item cleared without one is indistinguishable from one ignored.",
    userBenefit:
      "The investor is chased once, early, for exactly the right documents.",
    demoNote:
      "Note the basis check: Item L capital account is not §704(d) outside basis. Treating them as equal is a real-world error this catches.",
  },
  {
    id: "tieout",
    label: "Year-over-year tie-out",
    tier: "ops",
    parent: "assurance",
    sub: "materiality: $5,000 or 25%",
    icon: "loop",
    size: 6,
    what: "Compares every material line against the prior year and generates a narrative for each movement that crosses the materiality threshold.",
    whyUsed:
      "Scope item 7 is 'review the filings for consistency with prior years'. The point is not to make numbers match — it is that every number which moved has a sentence next to it before a reviewer signs.",
    clientBenefit:
      "A drop in K-1 count is flagged with both readings stated: an exit, which needs a §731 disposition analysis, or a document that has not arrived. Those lead to opposite actions, and guessing which is a coin flip nobody should be taking.",
    userBenefit:
      "The investor is told what changed and why before they have to ask.",
    demoNote:
      "The withholding variance explanation names the usual cause: the sponsor changed its assumption, or issued the 8805 to a different tier.",
  },
  {
    id: "audit",
    label: "Audit log",
    tier: "ops",
    parent: "assurance",
    sub: "append-only · who, when, on what facts",
    icon: "ledger",
    size: 6,
    what: "An append-only record of every consequential action: approvals with the signer's credential, overrides with their reason, field corrections with both the model's value and the human's, transmissions with submission ids.",
    whyUsed:
      "Circular 230 and any subsequent examination ask the same question — who decided this, when, and on what facts. A system that cannot answer it leaves the firm defending its process from memory.",
    clientBenefit:
      "Nothing in this table is ever updated or deleted. Every extraction correction stores the model's original alongside the human's value, which makes the audit trail double as the quality signal for whether extraction is drifting.",
    userBenefit:
      "The investor's file can answer questions about itself years later, without the original preparer.",
    demoNote:
      "Append-only, and the correction pairs do double duty: evidence for an examiner, and training signal for the prompt.",
  },
  {
    id: "deadlines",
    label: "Deadline tracking",
    tier: "ops",
    parent: "assurance",
    sub: "1120-F: June 15, not April 15",
    icon: "chart",
    size: 6,
    what: "Computes original and extended due dates per form, and defaults the engagement to extending everything.",
    whyUsed:
      "A foreign corporation with no U.S. office files Form 1120-F on the fifteenth day of the sixth month. Diary it as April 15 and the return is filed two months early on paper and late in reality when the K-1s slip.",
    clientBenefit:
      "Extensions are filed by default in March, so a late sponsor K-1 is an inconvenience rather than a penalty. Extending costs nothing; filing late accrues interest and penalties from the original date, and the extension is of time to file, not to pay.",
    userBenefit:
      "The investor never gets a late-filing notice because a sponsor was slow.",
    metric: { value: "Jun 15 → Dec 15", caption: "Form 1120-F original and extended dates, foreign corp with no U.S. office" },
    demoNote:
      "The sixth-month due date is the most commonly mis-diarised date in cross-border partnership work. It is asserted in a test.",
  },
  {
    id: "monitoring",
    label: "Monitoring",
    tier: "ops",
    parent: "assurance",
    sub: "structlog · request id bound",
    icon: "chart",
    size: 5,
    what: "Structured JSON logging with the request id and firm bound to every line, plus extraction metrics — fields per document, auto-accept rate, token usage per job.",
    whyUsed:
      "The operationally interesting question in this system is not latency, it is whether extraction quality is holding. That is only visible if auto-accept rate is recorded per prompt version.",
    clientBenefit:
      "A regression in extraction quality shows up as a rising review queue in the metrics, in the same week, rather than as an unexplained increase in preparer hours across a whole filing season.",
    userBenefit:
      "Nothing directly — but it is why the review burden does not quietly creep back up.",
    demoNote:
      "Auto-accept rate per prompt version is the metric that matters here, not p99 latency.",
  },

  // ==================================================== 7 · platform
  {
    id: "platform",
    label: "Platform",
    tier: "platform",
    parent: ROOT_ID,
    flowOrder: 7,
    sub: "workers · storage · migrations · tests",
    icon: "cluster",
    size: 9,
    what: "How the system runs: background workers for extraction, object storage for documents, versioned migrations, and a test suite that runs entirely offline.",
    whyUsed:
      "This work is violently seasonal. Five sponsors send K-1s in the same fortnight and then nothing happens for eight months, so the shape of the platform has to match that rather than a steady request rate.",
    clientBenefit:
      "Extraction runs off the request path, so a burst of twenty documents queues rather than timing out. The whole system runs on one modest box for a firm of this size — there is no GPU and no per-seat model licence in the cost base.",
    userBenefit:
      "Uploading twenty documents at once works, and the browser does not sit spinning while they are read.",
    demoNote:
      "Seasonality is the defining operational fact. Everything expensive is queued, and nothing expensive runs in a request.",
  },
  {
    id: "workers",
    label: "Background workers",
    tier: "platform",
    parent: "platform",
    sub: "arq · Redis",
    logo: "redis",
    icon: "cache",
    size: 5,
    what: "Runs classification and extraction asynchronously, plus the amended-document supersede job that retires an original K-1 when an amended one arrives.",
    whyUsed:
      "Extraction takes seconds to tens of seconds per document. Doing it in the upload request means timeouts during exactly the fortnight when everything arrives at once.",
    clientBenefit:
      "The API records intent and returns immediately; the worker does the work. Two live K-1s for the same partnership is how an amount gets counted twice, so superseding is a job rather than a hope.",
    userBenefit:
      "Uploads complete instantly regardless of how long the document takes to read.",
    demoNote:
      "The supersede job is small and unglamorous and prevents a whole class of double-counting.",
  },
  {
    id: "storage",
    label: "Document storage",
    tier: "platform",
    parent: "platform",
    sub: "S3-compatible · keys scoped by firm",
    icon: "archive",
    size: 5,
    what: "Documents live in object storage, never in the database, under content-addressed keys namespaced by firm and engagement.",
    whyUsed:
      "Prior-year returns and workpaper packages are large and immutable. Putting them in Postgres bloats every backup and makes restore times a function of how many years of PDFs a firm has accumulated.",
    clientBenefit:
      "Keys are namespaced by firm, so a leaked key from one tenant cannot even name another tenant's object. Backups stay small enough to restore quickly, which is the property that matters at 11pm on March 14th.",
    userBenefit:
      "Documents open quickly however many years of history the firm holds.",
    demoNote:
      "Content-addressed and firm-namespaced. The namespacing is a tenancy control, not just tidiness.",
  },
  {
    id: "migrations",
    label: "Schema migrations",
    tier: "platform",
    parent: "platform",
    sub: "Alembic · JSON for form shape",
    icon: "database",
    size: 5,
    what: "Versioned migrations, with K-1 line items stored as JSON keyed by form year rather than as ninety nullable columns.",
    whyUsed:
      "The K-1 changes shape between years — codes get added, boxes get renumbered. A column per box means a migration every filing season, forever.",
    clientBenefit:
      "A form change is a schema-version bump in a JSON payload rather than a migration against a table holding every client's history. That is the difference between supporting a new tax year in an afternoon and in a sprint.",
    userBenefit:
      "Nothing visible — but it is why the platform can support a new tax year before the season starts rather than during it.",
    demoNote:
      "JSON here is a considered trade, not laziness: the payload is versioned by form year so an old record still reads correctly.",
  },
  {
    id: "tests",
    label: "Test suite",
    tier: "platform",
    parent: "platform",
    sub: "61 tests · no network, no key",
    icon: "thumb",
    size: 7,
    what: "61 backend tests covering the rules, the workpapers, the filing gate, completeness detection and the tie-out — asserting conclusions and citations, not code paths.",
    whyUsed:
      "A rule that fires with the wrong requirement is worse than one that does not fire, because it looks like it worked. The tests check that the 1120-F due date is June, that the limitation stack runs in statutory order, and that the 8865 conclusion is recorded rather than omitted.",
    clientBenefit:
      "The whole suite runs with no network, no API key and no database — including the extraction pipeline, via a stub client. A firm can verify the engine's conclusions in CI without spending a cent on model calls or risking a test transmission.",
    userBenefit:
      "Nothing visible — this is the reason a rule change does not quietly break a conclusion that was right last year.",
    metric: { value: "61 tests", caption: "backend suite, all passing offline — measured in this repo" },
    demoNote:
      "End here. The page you are looking at is also tested — it renders with the API stopped, which is why this demo cannot fail because a service is cold.",
  },
];

// ---------------------------------------------------------------------------
// Links
// ---------------------------------------------------------------------------

export interface ArchLink {
  source: string;
  target: string;
  /**
   * `tree` is containment. `request` is the live path through the system. `context` is
   * data pulled into the engine, `data` is what it produces, `observe` is assurance,
   * and `improve` is the one loop that flows back upstream.
   */
  kind: "tree" | "request" | "context" | "data" | "observe" | "improve" | "platform";
  label?: string;
}

export const LINKS: ArchLink[] = [
  // The request path, stage by stage
  { source: "investor", target: "workspace", kind: "request", label: "uploads K-1s" },
  { source: "syndicators", target: "client-portal", kind: "request", label: "issues K-1 / K-3 / 8805" },
  { source: "workspace", target: "authn", kind: "request" },
  { source: "authn", target: "authz", kind: "request" },
  { source: "authz", target: "tenancy", kind: "request" },
  { source: "tenancy", target: "intake", kind: "request" },

  // Fact base assembly
  { source: "intake", target: "classifier", kind: "context" },
  { source: "classifier", target: "extractor", kind: "context" },
  { source: "extractor", target: "hitl", kind: "context" },
  { source: "hitl", target: "entity-graph", kind: "context" },
  { source: "carryforward", target: "entity-graph", kind: "context", label: "opening balances" },

  // Into the engine
  { source: "entity-graph", target: "engine", kind: "context", label: "fact base" },
  { source: "engine", target: "deterministic", kind: "data" },
  { source: "deterministic", target: "federal-rules", kind: "data" },
  { source: "deterministic", target: "state-rules", kind: "data" },
  { source: "deterministic", target: "crossborder-rules", kind: "data" },
  { source: "federal-rules", target: "protective", kind: "data" },
  { source: "state-rules", target: "composite-choice", kind: "data" },
  { source: "federal-rules", target: "authority", kind: "data" },
  { source: "crossborder-rules", target: "authority", kind: "data" },
  { source: "state-rules", target: "negative-findings", kind: "data" },

  // Out of the engine into the record
  { source: "authority", target: "workpapers", kind: "data", label: "citations" },
  { source: "engine", target: "record", kind: "data", label: "form matrix" },
  { source: "workpapers", target: "recon-1446", kind: "data" },
  { source: "workpapers", target: "deliverable", kind: "data" },
  { source: "record", target: "efile", kind: "data" },

  // Assurance
  { source: "efile", target: "filing-gate", kind: "observe", label: "blocked until clean" },
  { source: "recon-1446", target: "open-items", kind: "observe" },
  { source: "carryforward", target: "tieout", kind: "observe", label: "prior year" },
  { source: "filing-gate", target: "audit", kind: "observe" },
  { source: "override", target: "audit", kind: "observe" },
  { source: "open-items", target: "filing-gate", kind: "observe", label: "blocks" },
  { source: "tieout", target: "monitoring", kind: "observe" },
  { source: "deadlines", target: "workers", kind: "platform", label: "scheduled" },

  // Platform support
  { source: "workers", target: "extractor", kind: "platform" },
  { source: "storage", target: "intake", kind: "platform" },
  { source: "migrations", target: "record", kind: "platform" },
  { source: "tests", target: "engine", kind: "platform", label: "asserts conclusions" },

  // The improvement loop — the only edges flowing back upstream
  { source: "hitl", target: "extractor", kind: "improve", label: "corrections" },
  { source: "audit", target: "hitl", kind: "improve", label: "quality signal" },
];

// ---------------------------------------------------------------------------
// Derived
// ---------------------------------------------------------------------------

export const NODE_BY_ID = new Map(NODES.map((n) => [n.id, n]));
export const TIER_BY_ID = new Map(TIERS.map((t) => [t.id, t]));

export const CHILDREN_BY_PARENT = NODES.reduce((map, node) => {
  if (!node.parent) return map;
  const siblings = map.get(node.parent) ?? [];
  siblings.push(node);
  map.set(node.parent, siblings);
  return map;
}, new Map<string, ArchNode[]>());

export function hasChildren(id: string): boolean {
  return (CHILDREN_BY_PARENT.get(id)?.length ?? 0) > 0;
}

export function ancestorsOf(id: string): string[] {
  const chain: string[] = [];
  let current = NODE_BY_ID.get(id)?.parent;
  while (current) {
    chain.push(current);
    if (current === ROOT_ID) break;
    current = NODE_BY_ID.get(current)?.parent;
  }
  return chain;
}

/** Containment edges, derived from `parent` so the two can never disagree. */
export const TREE_LINKS: ArchLink[] = NODES.filter((n) => n.parent).map((n) => ({
  source: n.parent!,
  target: n.id,
  kind: "tree" as const,
}));

/** Top-level stages, in pipeline order. */
export const STAGES = NODES.filter((n) => n.flowOrder !== undefined).sort(
  (a, b) => a.flowOrder! - b.flowOrder!,
);

// ---------------------------------------------------------------------------
// Guided tour
// ---------------------------------------------------------------------------

export interface TourStop {
  nodeId: string;
  chapter: string;
  say: string;
}

export const TOUR: TourStop[] = [
  {
    nodeId: "investor",
    chapter: "1 · The problem",
    say: "A Canadian investor with five U.S. apartment syndications held through two Ontario holdcos. Every spring five K-1s arrive in five formats. The hard part is not the numbers — it is knowing which returns are owed and being able to prove why.",
  },
  {
    nodeId: "syndicators",
    chapter: "2 · Why it is hard",
    say: "The K-1s come from five sponsors on five schedules, and several arrive amended. Almost every delay and every defect in this work originates here, so the system is built around that fact rather than in spite of it.",
  },
  {
    nodeId: "signer",
    chapter: "3 · Who is accountable",
    say: "One credentialed CPA or EA signs. Their credential is a stored field, not a job title — and there is no code path that transmits a return without a recorded approval against a licensed user.",
  },
  {
    nodeId: "workspace",
    chapter: "4 · The workspace",
    say: "Six tabs, and each maps to one of the ten numbered items in the client's own scope of work. Tax software is built for keying a return; this is built for deciding, checking and evidencing.",
  },
  {
    nodeId: "review-queue",
    chapter: "5 · Review, not re-entry",
    say: "Twenty-seven fields per K-1, each with its confidence, its page and the line it came from. If checking a number means hunting through a forty-page PDF, the preparer starts trusting the model — and that is how a wrong figure reaches a filed return.",
  },
  {
    nodeId: "tenancy",
    chapter: "6 · Tenancy",
    say: "Every query filters on the firm from the token, never from the request body. Asking for another firm's engagement returns the same 404 as a record that does not exist — the distinction is itself a leak.",
  },
  {
    nodeId: "factbase",
    chapter: "7 · The boundary",
    say: "This stage turns PDFs into reviewed facts, and it is the boundary that matters most. Everything to the left is a model's proposal; everything to the right is evidence a professional will sign.",
  },
  {
    nodeId: "extractor",
    chapter: "8 · What the model does",
    say: "It reads documents. Parentheses mean negative, and a blank box is null rather than zero — because zero is an assertion and blank is an absence, and they lead to different determinations downstream.",
  },
  {
    nodeId: "hitl",
    chapter: "9 · The switch that matters",
    say: "Anything below 0.90 confidence goes to a person, and the human's value is stored alongside the model's rather than replacing it. That pair costs one column and gives the firm a measured auto-accept rate instead of a feeling.",
  },
  {
    nodeId: "carryforward",
    chapter: "10 · The memory",
    say: "Basis, at-risk, suspended losses and excess business interest carry forward per partnership. Pool the interest expense across the five syndications and the number is wrong every year afterwards, compounding.",
  },
  {
    nodeId: "engine",
    chapter: "11 · The engine",
    say: "Sixteen rules produce twenty-two determinations against this structure. This is the sentence from the client's own posting — someone who understands the underlying tax structure, not someone who enters K-1 numbers into software.",
  },
  {
    nodeId: "deterministic",
    chapter: "12 · Why it is not a model",
    say: "Every determination is ordinary Python, versioned by tax year. The same facts must produce the same forms in 2031 as in 2026, and any difference must be explainable by a change in facts — not by a vendor's model upgrade.",
  },
  {
    nodeId: "protective",
    chapter: "13 · The rule that pays for itself",
    say: "No income this year still means file a protective 1120-F. Without a timely return, section 882(c)(2) denies all deductions and the corporation is taxed on gross rental income. This one rule can outweigh the entire annual fee.",
  },
  {
    nodeId: "state-rules",
    chapter: "14 · Seven states",
    say: "Nexus follows the buildings, not the partnership's formation state. Texas gets examined despite having no income tax, and Tennessee franchise tax — the most commonly missed filing in multifamily portfolios — is caught by profile.",
  },
  {
    nodeId: "composite-choice",
    chapter: "15 · A decision, not a default",
    say: "The Georgia sponsor made a composite election without asking. Composite usually relieves the partner of a return and sometimes leaves them worse off, so both outcomes are computed rather than assumed.",
  },
  {
    nodeId: "crossborder-rules",
    chapter: "16 · The treaty",
    say: "Article X(6) cuts branch profits tax from thirty percent to five — but only for a qualifying person under the limitation-on-benefits article. Until that analysis is documented, the engine returns needs-analysis rather than a number.",
  },
  {
    nodeId: "negative-findings",
    chapter: "17 · The 8865 answer",
    say: "The client asked about Form 8865 by name. The engine records that it is the mirror image of this structure and does not apply, with the reasoning. Silence is not an answer to a question someone asked explicitly.",
  },
  {
    nodeId: "llm-determination",
    chapter: "18 · What we deliberately did not build",
    say: "We could let a model pick the forms directly. It would demo beautifully and it is not enabled, deliberately — a model-decided position cannot be reproduced across years or defended on examination, and the failure mode looks identical to success.",
  },
  {
    nodeId: "authority",
    chapter: "19 · Citations, as a by-product",
    say: "Every determination carries its statute, regulation or treaty article through to the workpaper and the memo. A determination you cannot cite is one you cannot defend, and reconstructing citations months later is a second job.",
  },
  {
    nodeId: "recon-1446",
    chapter: "20 · The check that earns its keep",
    say: "Sponsors withhold at the right rate and issue the 8805 to the wrong tier constantly. If the payee TIN is not the filer's, the credit is at risk — and at twenty-one percent on a six-figure allocation that is a five-figure cash item.",
  },
  {
    nodeId: "deliverable",
    chapter: "21 · What the client receives",
    say: "Filed returns, confirmations, workpapers and a plain-English memo — generated deterministically, so it exists even with no model reachable. The memo also names the Canadian items this engagement does not file.",
  },
  {
    nodeId: "filing-gate",
    chapter: "22 · The gate",
    say: "Four conditions, re-checked at transmission rather than trusted from approval, because an open item can be reopened in between. There is no override flag and no force parameter — deliberately.",
  },
  {
    nodeId: "open-items",
    chapter: "23 · Found in March, not November",
    say: "A missing K-3 found in March costs an email. Found in November it costs an amended return, which on a fixed fee is a re-run of the whole engagement for nothing.",
  },
  {
    nodeId: "deadlines",
    chapter: "24 · The date everyone gets wrong",
    say: "A foreign corporation with no U.S. office files the 1120-F on June the fifteenth, not April. Extensions are filed by default in March, so a slow sponsor is an inconvenience rather than a penalty.",
  },
  {
    nodeId: "audit",
    chapter: "25 · Proving what happened",
    say: "Append-only: approvals with the signer's credential, overrides with their reason, and every correction stored beside the model's original. That trail answers an examiner and doubles as the quality signal.",
  },
  {
    nodeId: "tests",
    chapter: "26 · How it is proven",
    say: "Sixty-one tests asserting conclusions and citations, all running with no network, no key and no database. This page is static for the same reason — a demo should never fail because a service is cold.",
  },
];

export { TIERS as ARCH_TIERS };
