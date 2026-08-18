"""Canadian-side advisory flags.

These are explicitly *not* filed by this engagement. They are raised because the
difference between a preparer and an advisor is whether the client hears about them
before the Canadian deadline rather than after it.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.models.enums import Requirement
from app.rules.base import SUPPORTED_YEARS, FactBase, RuleResult, registry

T1135_THRESHOLD_CAD = 100_000.0


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-CA-T1134", title="T1134 foreign affiliate reporting"
)
def rule_t1134(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if e.country != "CA" or not e.holds_us_partnership_interest:
            continue
        yield RuleResult(
            rule_id="R-CA-T1134",
            form="T1134 (advisory)",
            entity_id=e.entity_id,
            jurisdiction="canada_federal",
            requirement=Requirement.RECOMMENDED,
            rationale=(
                f"{e.name} is a Canadian corporation with interests in U.S. limited "
                f"partnerships. Depending on the ownership percentage and whether any "
                f"partnership is itself a foreign affiliate, a T1134 information return may "
                f"be due 10 months after year end. This is outside the U.S. engagement scope "
                f"and is flagged for the client's Canadian accountant, not prepared here."
            ),
            authority="Income Tax Act (Canada) s. 233.4",
            triggering_facts={"k1_count": e.k1_count},
            confidence=0.6,
        )


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-CA-T1135", title="T1135 foreign income verification"
)
def rule_t1135(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if e.country != "CA" or not e.holds_us_partnership_interest:
            continue
        yield RuleResult(
            rule_id="R-CA-T1135",
            form="T1135 (advisory)",
            entity_id=e.entity_id,
            jurisdiction="canada_federal",
            requirement=Requirement.RECOMMENDED,
            rationale=(
                f"Specified foreign property with a cost amount above CAD "
                f"{T1135_THRESHOLD_CAD:,.0f} requires a T1135. U.S. partnership interests "
                f"generally qualify. Advisory only — handed to the Canadian filer with the "
                f"U.S. cost-basis figures this engagement already produces, which is the "
                f"piece they usually have to ask for."
            ),
            authority="Income Tax Act (Canada) s. 233.3",
            triggering_facts={"threshold_cad": T1135_THRESHOLD_CAD},
            confidence=0.7,
        )


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-CA-FTC", title="Foreign tax credit coordination"
)
def rule_ftc(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if e.country != "CA":
            continue
        us_tax_paid = e.withholding_1446 + e.withholding_1445 + e.withholding_1042
        if us_tax_paid <= 0:
            continue
        yield RuleResult(
            rule_id="R-CA-FTC",
            form="Foreign tax credit memo (advisory)",
            entity_id=e.entity_id,
            jurisdiction="canada_federal",
            requirement=Requirement.RECOMMENDED,
            rationale=(
                f"${us_tax_paid:,.0f} of U.S. tax was withheld or paid by {e.name}. For the "
                f"structure to work economically that tax has to be creditable in Canada, and "
                f"the two systems recognise income in different periods — a U.S. amount paid "
                f"on a return filed in December can fall outside the Canadian year it relates "
                f"to. The exact figures and payment dates are supplied to the Canadian "
                f"accountant with the package so the credit is claimed in the right year."
            ),
            authority="Canada–U.S. Treaty Art. XXIV; ITA s. 126",
            triggering_facts={"us_tax_paid": us_tax_paid},
            confidence=0.8,
        )
