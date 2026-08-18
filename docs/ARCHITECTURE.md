# Architecture

The interactive version of this document is the **Architecture** tab in the app
(`/architecture`) — a 3D pipeline where every component states what it does, what breaks
without it, what it saves the firm and what the investor feels. This file is the written
companion for people who want it in a diff.

![Architecture explorer](img/07-architecture.png)

Clicking a stage isolates it. Below, the determination engine with its ten parts — the
click the whole walkthrough is built around:

![Determination engine expanded](img/08-architecture-engine.png)

A 26-stop guided tour walks the argument in pipeline order, including the stop covering
what was deliberately not built:

![Guided tour](img/09-architecture-tour.png)

## The pipeline

```
People → Workspace → Access → Fact base → Determination → Returns & record
       → Assurance → Platform
```

| Stage | What happens | Where it lives |
|---|---|---|
| **People** | Investor, preparer, credentialed signer, and the five syndicators who issue the documents | — |
| **Workspace** | Engagement dashboard, extraction review, determinations, workpapers, open items, filings | `frontend/app` |
| **Access** | Authentication, role authorization, firm scoping | `backend/app/api/deps.py` |
| **Fact base** | Intake and dedupe, classification, extraction, human confirmation, entity graph, carryforwards | `backend/app/services/{extraction,factbase}.py` |
| **Determination** | 16 versioned rules producing a cited per-entity form matrix | `backend/app/rules/` |
| **Returns & record** | Workpapers, form assembly, e-file transmission, client package | `backend/app/services/{workpapers,efile,memo}.py` |
| **Assurance** | Filing gate, open items, year-over-year tie-out, audit log, deadlines | `backend/app/services/{completeness,tieout,efile}.py` |
| **Platform** | Workers, object storage, migrations, tests | `backend/app/workers/`, `backend/alembic/` |

## Three decisions worth arguing about

### 1. Determination is deterministic Python, not a model

The model reads documents. It does not decide filing positions.

A tax position has to be reproducible: the same facts must produce the same forms in 2031
as in 2026, and any difference between two years must be explainable by a change in facts
rather than a change in model weights. Rules are registered per tax year
(`RuleSet(2024)`, `RuleSet(2025)`, `RuleSet(2026)` coexist), so re-running a prior year
reproduces that year's answer.

Every rule emits its authority — IRC section, Treasury regulation, treaty article, form
instruction — and that citation flows through the workpaper into the client memo. A
determination you cannot cite is one you cannot defend.

The infrastructure to let a model decide requirements directly exists and is deliberately
not wired in. See `llm-determination` on the Architecture tab for the reasoning.

### 2. Nothing reaches a return without passing through a reviewed state

Extraction produces a confidence per field. Anything below `0.90` is routed to a human,
and the human's value is stored **alongside** the model's original rather than replacing
it. That pair costs one column and gives the firm a measured auto-accept rate per prompt
version — without it, a quiet regression survives an entire filing season.

### 3. The filing gate is an object, not a set of `if`s

`FilingGate.assert_transmittable` checks four conditions: the return is approved, the
approver is a reviewer, the approver holds a credential, and no blocking open item is
outstanding. Every transmission path calls it, and there is no override parameter.

Conditions are re-checked **at transmission**, not trusted from approval, because an open
item can be reopened in between.

## Data model

```
Firm ──< User
Firm ──< Client ──< Entity ──< Ownership (owner → owned)
                       └──< PropertyState        (state nexus driver)
Client ──< Engagement ──< Document ──< ExtractionJob ──< ExtractedField
                    ├──< K1Record                (the reviewed fact base)
                    ├──< Determination           (one rule firing, with authority)
                    ├──< Filing ──> submission / acknowledgement
                    ├──< Workpaper
                    ├──< OpenItem
                    ├──< Variance
                    └──< Deliverable
AuditEvent — append-only, never updated or deleted
```

Two modelling choices to note:

- **Ownership carries profits and capital percentages separately.** They diverge sharply
  in a syndication waterfall and they drive different rules.
- **K-1 line items are JSON keyed by `form_year`, not 90 nullable columns.** The form
  changes shape between years; a column per box means a migration every filing season.

## Idempotency

`run_determination` can be re-run at any time. It replaces computed output — determinations,
workpapers, variances — but **preserves every human decision**: reviewer overrides,
resolved open items and approved filings all survive. A re-run that discarded someone's
judgement would be a re-run staff learn to avoid, and stale determinations then get filed.

## Testing

61 backend tests and 42 frontend tests, all running with **no network, no database and no
API key**. The extraction pipeline runs against `StubExtractionClient` and e-file against
`StubTransmitter`, so no test can reach a model API or the IRS.

The tests assert conclusions, not code paths: that the 1120-F is due in the sixth month,
that the loss limitation stack runs §704(d) → §465 → §469, that the Form 8865 conclusion
is recorded rather than omitted, and that the filing gate reports every blocker at once.
