"""Client memo — engagement deliverable: "a brief summary of any material tax issues".

Structure is generated deterministically; only the prose polish is optional. A memo that
depends on a model being reachable is a memo that fails on the day it is needed.
"""

from __future__ import annotations

from app.rules.base import FactBase, RuleResult
from app.services.tieout import VarianceDraft


def build_memo(
    facts: FactBase,
    results: list[RuleResult],
    variances: list[VarianceDraft],
    client_name: str,
) -> str:
    required = [r for r in results if r.requirement.value in {"required", "protective"}]
    federal = [r for r in required if r.jurisdiction == "us_federal"]
    state = [r for r in required if r.jurisdiction == "us_state"]
    advisory = [r for r in results if r.jurisdiction.startswith("canada")]
    judgement = [r for r in results if r.requirement.value == "needs_analysis"]
    negatives = [r for r in results if r.requirement.value == "not_required"]

    names = {e.entity_id: e.name for e in facts.entities}
    total_eci = sum(e.rental_income + e.ordinary_income + e.usrpi_gain for e in facts.entities)
    total_wh = sum(e.withholding_1446 for e in facts.entities)
    k1_total = sum(e.k1_count for e in facts.entities)

    lines: list[str] = [
        f"# {facts.tax_year} U.S. tax filing summary — {client_name}",
        "",
        "## What was filed",
        "",
        f"{len(federal)} U.S. federal return(s) and {len(state)} state return(s) were prepared "
        f"from {k1_total} Schedule K-1s. Aggregate effectively connected income was "
        f"${total_eci:,.0f}, against ${total_wh:,.0f} of §1446 withholding claimed as a credit.",
        "",
    ]

    for r in federal:
        lines.append(f"**{r.form} — {names.get(r.entity_id, r.entity_id)}**")
        lines.append("")
        lines.append(r.rationale)
        lines.append("")
        lines.append(f"*Authority: {r.authority}*")
        lines.append("")

    if state:
        lines += ["## State filings", ""]
        for r in state:
            lines.append(
                f"- **{r.state} — {r.form}** ({names.get(r.entity_id, '')}): {r.rationale}"
            )
        lines.append("")

    if judgement:
        lines += [
            "## Items that required a judgement call",
            "",
            "These are positions rather than mechanics. Each was decided deliberately and the "
            "reasoning is recorded in the workpapers.",
            "",
        ]
        for r in judgement:
            lines.append(f"- **{r.form}**: {r.rationale}")
        lines.append("")

    if negatives:
        lines += [
            "## Considered and not required",
            "",
            "Recorded so you can see the question was asked rather than skipped.",
            "",
        ]
        for r in negatives:
            lines.append(f"- **{r.form}** — {names.get(r.entity_id, '')}: {r.rationale}")
        lines.append("")

    material = [v for v in variances if v.is_material]
    if material:
        lines += ["## What changed from last year", ""]
        for v in material:
            lines.append(f"- **{names.get(v.entity_id, '')} — {v.metric}**: {v.explanation}")
        lines.append("")

    if advisory:
        lines += [
            "## Canadian-side items for your Canadian accountant",
            "",
            "Outside the scope of this U.S. engagement, flagged so nothing falls between the "
            "two advisors.",
            "",
        ]
        for r in advisory:
            lines.append(f"- **{r.form}**: {r.rationale}")
        lines.append("")

    lines += [
        "## For next year",
        "",
        "- The structure is unchanged, so next year is a re-run of this determination against "
        "new K-1s rather than a fresh analysis.",
        "- The single biggest driver of cost and timing remains K-1 arrival dates. Extensions "
        "are filed by default in March so a late K-1 is an inconvenience, not a penalty.",
        "- Carryforward balances (suspended losses, EBIE, basis) are tracked per partnership "
        "and roll forward automatically.",
    ]
    return "\n".join(lines)
