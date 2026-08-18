"""Workpaper generation.

Every schedule is reproducible from the fact base. Nothing here is hand-keyed, which is
what makes year two cheap and what makes an examination survivable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rules.base import EntityFacts, FactBase, RuleResult

GENERATOR_VERSION = "wp-2025.2"


@dataclass
class WorkpaperDraft:
    code: str
    title: str
    entity_id: str | None
    rows: list[dict] = field(default_factory=list)
    totals: dict = field(default_factory=dict)
    narrative: str = ""
    ties_out: bool = True
    tie_out_detail: dict = field(default_factory=dict)


def wp_k1_summary(facts: FactBase, entity: EntityFacts) -> WorkpaperDraft:
    """WP-K1 — every K-1 in one grid, which is how a reviewer spots the odd one out."""
    rows = [
        {
            "line": "Net rental real estate income (box 2)",
            "amount": entity.rental_income,
            "character": "ECI",
        },
        {
            "line": "Ordinary business income (box 1)",
            "amount": entity.ordinary_income,
            "character": "ECI",
        },
        {
            "line": "Interest and dividends (boxes 5, 6a)",
            "amount": entity.fdap_income,
            "character": "FDAP unless §882(d) election",
        },
        {
            "line": "Capital and §1231 gain (boxes 9a, 10)",
            "amount": entity.capital_gain,
            "character": "ECI to the extent §897 applies",
        },
        {
            "line": "§897 / USRPI gain (box 20 AH)",
            "amount": entity.usrpi_gain,
            "character": "ECI — §897(a)",
        },
        {
            "line": "Excess business interest expense (box 13 K)",
            "amount": -entity.excess_business_interest,
            "character": "Suspended — §163(j)",
        },
    ]
    total_eci = entity.rental_income + entity.ordinary_income + entity.usrpi_gain
    return WorkpaperDraft(
        code="WP-K1",
        title=f"K-1 summary — {entity.name} ({entity.k1_count} partnerships)",
        entity_id=entity.entity_id,
        rows=rows,
        totals={
            "effectively_connected_income": total_eci,
            "fdap_income": entity.fdap_income,
            "k1_count": entity.k1_count,
            "k3_count": entity.k3_count,
        },
        narrative=(
            f"{entity.k1_count} Schedule K-1s were received for {entity.name} for "
            f"{facts.tax_year}, of which {entity.k3_count} were accompanied by a Schedule "
            f"K-3. Aggregate effectively connected income is ${total_eci:,.0f}."
            + (
                ""
                if entity.k3_count >= entity.k1_count
                else f" {entity.k1_count - entity.k3_count} partnership(s) have not supplied "
                f"a K-3; the source and character detail it carries is what supports the "
                f"1120-F presentation, so those are tracked as open items rather than "
                f"estimated."
            )
        ),
        ties_out=entity.k3_count >= entity.k1_count,
        tie_out_detail={"k1_count": entity.k1_count, "k3_count": entity.k3_count},
    )


def wp_1446_reconciliation(facts: FactBase, entity: EntityFacts) -> WorkpaperDraft:
    """WP-1446 — the credit only survives if the 8805 payee matches the filer."""
    rate = 0.21
    expected = max(entity.rental_income + entity.ordinary_income, 0.0) * rate
    actual = entity.withholding_1446
    delta = actual - expected
    ties = abs(delta) <= max(500.0, expected * 0.05)

    return WorkpaperDraft(
        code="WP-1446",
        title=f"§1446 withholding reconciliation — {entity.name}",
        entity_id=entity.entity_id,
        rows=[
            {"line": "Effectively connected taxable income allocated", "amount": expected / rate},
            {"line": f"Expected withholding at {rate:.0%}", "amount": expected},
            {"line": "Withholding per Forms 8805 / K-1 box 15 code O", "amount": actual},
            {"line": "Difference", "amount": delta},
        ],
        totals={"expected": expected, "actual": actual, "difference": delta},
        narrative=(
            f"Forms 8805 report ${actual:,.0f} of §1446 withholding against expected "
            f"withholding of ${expected:,.0f} at the {rate:.0%} corporate rate. "
            + (
                "The amounts agree within tolerance and the credit is claimed as filed."
                if ties
                else f"The ${abs(delta):,.0f} difference must be resolved before filing. The "
                f"usual cause is an 8805 issued to the wrong tier of the structure — if the "
                f"payee TIN is not the filing entity's, the credit is at risk and only the "
                f"partnership can correct it."
            )
        ),
        ties_out=ties,
        tie_out_detail={"tolerance": max(500.0, expected * 0.05), "delta": delta},
    )


def wp_basis_at_risk(facts: FactBase, entity: EntityFacts) -> WorkpaperDraft:
    """WP-BASIS — the limitation stack, applied in statutory order."""
    loss = abs(entity.allocated_loss)
    after_704d = min(loss, entity.outside_basis)
    suspended_704d = loss - after_704d
    after_465 = min(after_704d, entity.at_risk_amount)
    suspended_465 = after_704d - after_465

    return WorkpaperDraft(
        code="WP-BASIS",
        title=f"Loss limitation stack — {entity.name}",
        entity_id=entity.entity_id,
        rows=[
            {"line": "Allocated loss", "amount": -loss},
            {"line": "Outside basis before loss (§704(d))", "amount": entity.outside_basis},
            {"line": "Loss allowed after §704(d)", "amount": -after_704d},
            {"line": "Suspended — §704(d)", "amount": -suspended_704d},
            {
                "line": "At-risk amount incl. qualified nonrecourse (§465(b)(6))",
                "amount": entity.at_risk_amount,
            },
            {"line": "Loss allowed after §465", "amount": -after_465},
            {"line": "Suspended — §465", "amount": -suspended_465},
            {"line": "Remaining loss subject to §469 passive limitation", "amount": -after_465},
        ],
        totals={
            "allowed": after_465,
            "suspended_704d": suspended_704d,
            "suspended_465": suspended_465,
            "qualified_nonrecourse": entity.qualified_nonrecourse_debt,
        },
        narrative=(
            f"${loss:,.0f} of allocated loss runs the limitation stack in statutory order. "
            f"${entity.qualified_nonrecourse_debt:,.0f} of qualified nonrecourse financing is "
            f"treated as at-risk under §465(b)(6) — the real-estate exception that makes the "
            f"at-risk step pass here where it would fail for ordinary nonrecourse debt. "
            f"${after_465:,.0f} survives to the §469 passive test; ${suspended_704d:,.0f} is "
            f"suspended under §704(d) and releases only against future basis, and "
            f"${suspended_465:,.0f} is suspended under §465 and releases only against future "
            f"at-risk amount. The buckets are not interchangeable."
        ),
        ties_out=True,
    )


def wp_state_matrix(
    facts: FactBase, entity: EntityFacts, results: list[RuleResult]
) -> WorkpaperDraft:
    """WP-STATE — every state the property touches, with the conclusion for each."""
    state_results = [
        r
        for r in results
        if r.jurisdiction == "us_state" and r.entity_id == entity.entity_id
    ]
    rows = [
        {
            "state": r.state,
            "form": r.form,
            "requirement": r.requirement.value,
            "income": entity.state_amounts.get(r.state or "", 0.0),
            "composite": (r.state in entity.composite_states),
            "due_date": r.due_date.isoformat() if r.due_date else None,
            "authority": r.authority,
        }
        for r in state_results
    ]
    required = [r for r in rows if r["requirement"] == "required"]
    return WorkpaperDraft(
        code="WP-STATE",
        title=f"State filing matrix — {entity.name}",
        entity_id=entity.entity_id,
        rows=rows,
        totals={
            "states_examined": len(rows),
            "returns_required": len(required),
            "total_state_income": sum(entity.state_amounts.values()),
        },
        narrative=(
            f"{len(rows)} states were examined based on the situs of the underlying property, "
            f"not the formation state of the partnerships. {len(required)} require a return. "
            f"States examined and concluded not to require a filing are listed here as well, "
            f"so next year's preparer can see the threshold that was tested rather than "
            f"re-deriving it."
        ),
        ties_out=True,
    )


def wp_determination_index(
    facts: FactBase, results: list[RuleResult], coverage: dict
) -> WorkpaperDraft:
    """WP-INDEX — the assurance list: every rule considered, and its conclusion."""
    by_rule: dict[str, list[RuleResult]] = {}
    for r in results:
        by_rule.setdefault(r.rule_id, []).append(r)

    rows = [
        {
            "rule_id": rule_id,
            "title": title,
            "fired": rule_id in by_rule,
            "conclusions": [
                {
                    "entity_id": r.entity_id,
                    "form": r.form,
                    "requirement": r.requirement.value,
                    "authority": r.authority,
                }
                for r in by_rule.get(rule_id, [])
            ],
        }
        for rule_id, title in sorted(coverage.items())
    ]
    return WorkpaperDraft(
        code="WP-INDEX",
        title=f"Determination index — tax year {facts.tax_year}",
        entity_id=None,
        rows=rows,
        totals={
            "rules_evaluated": len(coverage),
            "determinations": len(results),
            "required": sum(1 for r in results if r.requirement.value == "required"),
            "protective": sum(1 for r in results if r.requirement.value == "protective"),
            "not_required": sum(1 for r in results if r.requirement.value == "not_required"),
            "needs_analysis": sum(1 for r in results if r.requirement.value == "needs_analysis"),
        },
        narrative=(
            f"All {len(coverage)} rules in the {facts.tax_year} rule set were evaluated against "
            f"this structure. Rules that concluded no filing is required are listed with their "
            f"reasoning — a documented negative conclusion is a deliverable, and it is what "
            f"makes next year's review a comparison rather than a fresh analysis."
        ),
        ties_out=True,
    )


def generate_all(
    facts: FactBase, results: list[RuleResult], coverage: dict
) -> list[WorkpaperDraft]:
    drafts: list[WorkpaperDraft] = []
    for entity in facts.entities:
        if not entity.holds_us_partnership_interest:
            continue
        drafts.append(wp_k1_summary(facts, entity))
        if entity.withholding_1446 > 0:
            drafts.append(wp_1446_reconciliation(facts, entity))
        if entity.allocated_loss < 0:
            drafts.append(wp_basis_at_risk(facts, entity))
        if entity.property_states:
            drafts.append(wp_state_matrix(facts, entity, results))
    drafts.append(wp_determination_index(facts, results, coverage))
    return drafts
