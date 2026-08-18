"""Open-item detection — engagement scope item 8.

Finding a missing K-3 in March costs an email. Finding it in November costs an amended
return, so every check here runs continuously rather than once at the end.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import IssueSeverity
from app.rules.base import FactBase, RuleResult


@dataclass
class OpenItemDraft:
    code: str
    title: str
    detail: str
    severity: IssueSeverity
    entity_id: str | None = None
    blocks_filing: bool = False
    requested_from: str | None = None


def detect(
    facts: FactBase, results: list[RuleResult], expected_k1_count: dict[str, int]
) -> list[OpenItemDraft]:
    items: list[OpenItemDraft] = []

    for e in facts.entities:
        if not e.holds_us_partnership_interest:
            continue

        expected = expected_k1_count.get(e.entity_id, 0)
        if expected and e.k1_count < expected:
            items.append(
                OpenItemDraft(
                    code="MISSING_K1",
                    title=f"{expected - e.k1_count} of {expected} K-1s not yet received",
                    detail=(
                        f"{e.name} holds interests in {expected} partnerships but only "
                        f"{e.k1_count} Schedule K-1s have been received and accepted. The "
                        f"return cannot be filed complete without them, and filing without "
                        f"one means amending later."
                    ),
                    severity=IssueSeverity.BLOCKING,
                    entity_id=e.entity_id,
                    blocks_filing=True,
                    requested_from="syndicator",
                )
            )

        if e.k1_count and e.k3_count < e.k1_count:
            items.append(
                OpenItemDraft(
                    code="MISSING_K3",
                    title=f"{e.k1_count - e.k3_count} Schedule K-3(s) outstanding",
                    detail=(
                        "A K-3 carries the source and character detail that supports the "
                        "1120-F presentation for a foreign partner. Without it the ECI/FDAP "
                        "split rests on inference rather than on the partnership's own "
                        "reporting, which is a weak position to defend."
                    ),
                    severity=IssueSeverity.BLOCKING,
                    entity_id=e.entity_id,
                    blocks_filing=True,
                    requested_from="syndicator",
                )
            )

        if e.withholding_1446 > 0 and not e.us_tin:
            items.append(
                OpenItemDraft(
                    code="MISSING_EIN",
                    title=f"{e.name} has no U.S. TIN on file",
                    detail=(
                        f"${e.withholding_1446:,.0f} of §1446 withholding is being claimed as "
                        f"a credit, but the entity has no U.S. EIN recorded. The credit cannot "
                        f"be claimed and the return cannot be e-filed without one — an SS-4 "
                        f"takes weeks by fax for a foreign applicant, so this is raised early "
                        f"rather than at the deadline."
                    ),
                    severity=IssueSeverity.BLOCKING,
                    entity_id=e.entity_id,
                    blocks_filing=True,
                    requested_from="client",
                )
            )

        if e.treaty_lob_qualified is None:
            items.append(
                OpenItemDraft(
                    code="LOB_UNDOCUMENTED",
                    title=f"Treaty limitation-on-benefits analysis missing for {e.name}",
                    detail=(
                        "Article X(6) reduces branch profits tax from 30% to 5%, but only for "
                        "a qualifying person under Article XXIX-A. Until the LOB analysis is "
                        "documented the reduced rate cannot be claimed, and on these amounts "
                        "the difference is the largest single number in the return."
                    ),
                    severity=IssueSeverity.WARNING,
                    entity_id=e.entity_id,
                    requested_from="client",
                )
            )

        if e.outside_basis <= 0 and e.k1_count:
            items.append(
                OpenItemDraft(
                    code="BASIS_UNKNOWN",
                    title=f"No opening tax basis established for {e.name}",
                    detail=(
                        "Capital account per Item L is book/tax-basis capital, not outside "
                        "basis — they differ by the partner's share of liabilities and by any "
                        "purchase premium. Without an established opening outside basis the "
                        "§704(d) limitation cannot be computed and distributions cannot be "
                        "tested for gain under §731."
                    ),
                    severity=IssueSeverity.WARNING,
                    entity_id=e.entity_id,
                    requested_from="client",
                )
            )

    for r in results:
        if r.requirement.value == "needs_analysis":
            items.append(
                OpenItemDraft(
                    code=f"ANALYSIS_{r.rule_id}",
                    title=f"{r.form} requires a judgement call",
                    detail=r.rationale,
                    severity=IssueSeverity.WARNING,
                    entity_id=r.entity_id,
                    blocks_filing=r.jurisdiction == "us_federal",
                )
            )

    return items
