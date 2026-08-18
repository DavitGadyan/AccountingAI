# AccountingAI — Cross-Border Syndication Tax Compliance Platform

## 1. The problem, stated from the engagement

A Canadian investor holds LP interests in ~5 U.S. multifamily syndications through **two
Canadian holding companies**. Every spring a pile of Schedule K-1s (Form 1065) and K-3s
arrives from five different syndicators, in five different formats, on five different
schedules — most of them late, several of them amended.

Someone then has to answer questions that no tax software asks:

- Does a Canadian corporation holding an LP interest in a U.S. partnership that owns
  U.S. real property have **effectively connected income**? (Yes — §897(a), §875(1).)
- Does that create a **Form 1120-F** filing obligation, and is a **protective return**
  under Reg. §1.882-4(a)(3)(vi) needed for the entities with no current ECI?
- Was §1446 withholding done, is there an **8805** for each holdco, and does the credit
  tie to the return?
- Is there a **branch profits tax** exposure under §884, and does Article X(6) of the
  Canada–U.S. treaty reduce it to 5%?
- Which of the **six states** the properties sit in require a nonresident return, and
  which were satisfied by a composite election the syndicator made without asking?
- Did anything trigger **§1446(f)** or **FIRPTA** withholding on a disposition?

The client's own words: *"someone who understands the underlying tax structure, not
someone who simply enters numbers from K-1s into tax software."*

That sentence is the product thesis. The numbers are the easy part; the **determination**
is the work, and it is the part that is identical every year for the same structure —
which makes it exactly the thing worth encoding once.

## 2. What the platform is

A vertical workflow system for CPA/EA firms doing U.S. compliance for non-U.S. investors
in U.S. real-estate partnerships. It runs an engagement end to end:

```
Intake → Extraction → Structure → Determination → Preparation → Review → File → Deliver
```

Six of those eight stages are automated. Two of them — **Review** and **File** — require a
credentialed human to sign, by design and by Circular 230. The platform never files
anything a preparer has not approved.

## 3. Scope of work → system capability

The engagement's ten numbered scope items map one-to-one onto the build. This is the
acceptance criteria for v1.

| # | Engagement scope item | Platform capability |
|---|---|---|
| 1 | Review prior-year returns and existing structure | Prior-year return ingest; entity/ownership graph builder; carryforward extraction (basis, §704(d), §465 at-risk, §469 PAL, §163(j) EBIE) |
| 2 | Review annual K-1s and related documents | Document intake, classification, K-1/K-3 line-level extraction with confidence scores and page/box provenance |
| 3 | Determine U.S. federal filing requirements | Deterministic rules engine over the entity graph — outputs a per-entity form matrix with authority citations |
| 4 | Prepare and e-file federal returns and information returns | Return assembly, workpaper generation, MeF transmitter adapter, acknowledgement tracking |
| 5 | Prepare applicable state filings | State nexus/apportionment engine driven by K-1 state supplements and property situs |
| 6 | Cross-border/international information reporting | 1120-F, 5472, 8833, 8804/8805, 1042-S, 8288-A, 8865 determination and preparation |
| 7 | Review filings for consistency with prior years | Year-over-year tie-out: variance detection on every material line with a materiality threshold |
| 8 | Identify missing information before filing | Completeness engine — open-item list generated from expected-vs-received documents and unresolved dependencies |
| 9 | Provide completed copies and supporting schedules | Deliverable package builder — filed returns, confirmations, workpapers, index |
| 10 | Respond to follow-up questions | Engagement memo generator + a grounded Q&A surface over the client's own filed record |

## 4. Users

| Role | What they do here |
|---|---|
| **Preparer** | Works the queue: reviews extractions, resolves open items, prepares returns |
| **Reviewer / Signer** (CPA/EA) | Approves determinations, signs returns, authorises transmission. The only role that can file |
| **Firm admin** | Clients, engagements, fixed-fee terms, users, billing |
| **Client (investor)** | Uploads documents to a portal, sees status, receives the deliverable package |

Everything is tenant-scoped to a firm. A preparer cannot see another firm's data, and
role checks are enforced server-side on every route, not in the UI.

## 5. The determination engine — the defensible core

Filing determination is **deterministic Python, not an LLM**. This is a deliberate and
load-bearing decision:

- A tax position must be reproducible. The same facts must produce the same forms in
  2026 as in 2031, and a diff between two years must be explainable by a change in facts,
  not by a change in model weights.
- Every rule carries its **authority** (IRC §, Treas. Reg., treaty article, form
  instruction) and emits it into the workpaper. A determination you cannot cite is a
  determination you cannot defend under examination.
- Rules are versioned by tax year. `RuleSet(2025)` and `RuleSet(2026)` coexist, so
  re-running a prior year reproduces the prior year's answer.

The LLM does the work LLMs are actually good at, and only that:

- **Classify** an unlabeled PDF ("this is a 2025 K-3 Part IV from Sunbelt Apartment
  Fund III").
- **Extract** line items into a typed schema, with a confidence per field and a page
  reference so a human can check it in two seconds.
- **Draft prose** — the plain-English client memo, the variance narrative — which a human
  edits and signs.

Any field below the confidence threshold goes to a human. No extraction reaches a return
without passing through a reviewed state. See `docs/TAX_RULES.md` for the full rule set.

## 6. Non-goals for v1

Stated explicitly, because scope creep in tax software is how you end up rebuilding
Lacerte badly:

- **Not a tax calculation engine for the full IRC.** It determines, assembles, and
  ties out. Final computation lives in the forms.
- **Not Canadian domestic compliance.** T2, T1134, T1135 and FAPI exposure are *flagged
  as advisory items* in the memo, and handed to the client's Canadian accountant.
- **Not a bookkeeping system.** These are passive investments with no operating cash flow
  the client manages. There is no general ledger here.
- **Not an IRS-authorized transmitter.** The platform integrates with one through a
  documented adapter interface; it does not become one.
- **Not unsupervised filing.** There is no path through the system that transmits a return
  without a credentialed human approval event recorded against their user id.

## 7. Success measures

| Measure | Target | Why it is the right measure |
|---|---|---|
| Preparer hours per engagement-year | 12h → 3h | The engagement is fixed-fee; hours are the entire margin |
| Extraction fields accepted without edit | > 92% | Below this, review costs more than manual entry |
| Open items found before filing, not after | > 95% | A missing K-3 discovered post-filing is an amended return |
| Year-2 setup time for an existing client | < 30 min | The structure is unchanged; year 2 should be a re-run |
| Determinations changed by reviewer | Tracked, not minimised | A reviewer who never overrides is a reviewer who is not reading |
