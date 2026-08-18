"""U.S. federal determination rules.

Each rule is small, pure, and cites its authority. Read alongside ``docs/TAX_RULES.md``,
which is the prose version of this file.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.models.enums import Requirement
from app.rules.base import SUPPORTED_YEARS, EntityFacts, FactBase, RuleResult, registry
from app.rules.calendar import extended_due_date, form_due_date

FOREIGN_CORP_TYPES = {"ca_corporation"}
US_PARTNERSHIP_TYPES = {"us_partnership", "us_llc"}


def _is_foreign_corp(e: EntityFacts) -> bool:
    return e.entity_type in FOREIGN_CORP_TYPES or e.tax_classification == "foreign_corporation"


def _dated(form: str, tax_year: int, **kw) -> dict:
    return {
        "due_date": form_due_date(form, tax_year, **kw),
        "extended_due_date": extended_due_date(form, tax_year, **kw),
    }


# --------------------------------------------------------------------------------------
# Form 1120-F — the return the whole engagement turns on
# --------------------------------------------------------------------------------------
@registry.register(
    years=SUPPORTED_YEARS,
    rule_id="R-1120F-ECI",
    title="Foreign corporation with effectively connected income",
)
def rule_1120f_eci(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if not _is_foreign_corp(e) or not e.holds_us_partnership_interest:
            continue

        eci = e.eci_income + e.rental_income + e.ordinary_income + e.usrpi_gain
        has_eci = abs(eci) > 0.005 or e.withholding_1446 > 0

        if has_eci:
            yield RuleResult(
                rule_id="R-1120F-ECI",
                form="1120-F",
                entity_id=e.entity_id,
                requirement=Requirement.REQUIRED,
                rationale=(
                    f"{e.name} is a non-U.S. corporation holding an interest in a U.S. "
                    f"partnership engaged in a U.S. trade or business. Under §875(1) the "
                    f"partner is itself treated as engaged in that trade or business, so the "
                    f"allocated income of ${eci:,.0f} is effectively connected and Form "
                    f"1120-F is required on a net basis."
                ),
                authority=(
                    "IRC §882(a); IRC §875(1); IRC §897(a); "
                    "Treas. Reg. §1.6012-2(g); Form 1120-F instructions"
                ),
                triggering_facts={
                    "eci_income": eci,
                    "withholding_1446": e.withholding_1446,
                    "k1_count": e.k1_count,
                },
                **_dated("1120-F", facts.tax_year),
            )
        else:
            # No ECI this year — but filing nothing risks §882(c)(2).
            yield RuleResult(
                rule_id="R-1120F-PROTECTIVE",
                form="1120-F",
                entity_id=e.entity_id,
                requirement=Requirement.PROTECTIVE,
                rationale=(
                    f"{e.name} holds a U.S. partnership interest but no effectively "
                    f"connected income was allocated for {facts.tax_year}. A protective "
                    f"Form 1120-F should still be filed: without a timely return, §882(c)(2) "
                    f"denies all deductions and credits, and the corporation would be taxed "
                    f"on gross rather than net ECI in any year the position is challenged. "
                    f"The cost of the protective return is trivial against that exposure."
                ),
                authority="Treas. Reg. §1.882-4(a)(3)(vi); IRC §882(c)(2)",
                triggering_facts={"eci_income": 0.0, "k1_count": e.k1_count},
                confidence=0.95,
                **_dated("1120-F", facts.tax_year),
            )


@registry.register(
    years=SUPPORTED_YEARS,
    rule_id="R-BRANCH-PROFITS",
    title="Branch profits tax and treaty rate",
)
def rule_branch_profits(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if not _is_foreign_corp(e) or not e.holds_us_partnership_interest:
            continue
        eci = e.eci_income + e.rental_income + e.ordinary_income
        if eci <= 0:
            continue

        treaty_ok = e.treaty_country == "US" or e.treaty_country == "CA"
        qualified = bool(e.treaty_lob_qualified)
        yield RuleResult(
            rule_id="R-BRANCH-PROFITS",
            form="1120-F Sch. I",
            entity_id=e.entity_id,
            requirement=Requirement.REQUIRED if qualified else Requirement.NEEDS_ANALYSIS,
            rationale=(
                f"Branch profits tax applies to {e.name}'s dividend-equivalent amount. "
                + (
                    "Article X(6) of the Canada–U.S. treaty reduces the statutory 30% rate "
                    "to 5%, and the limitation-on-benefits analysis under Article XXIX-A is "
                    "documented as satisfied."
                    if qualified
                    else "The 5% treaty rate under Article X(6) is available only if the "
                    "corporation is a qualifying person under Article XXIX-A. That "
                    "limitation-on-benefits analysis has not been recorded for this entity, "
                    "so the rate cannot be claimed yet — at 30% the difference is material."
                )
            ),
            authority=(
                "IRC §884(a); Canada–U.S. Income Tax Convention Art. X(6), Art. XXIX-A"
            ),
            triggering_facts={"eci": eci, "lob_qualified": qualified, "treaty": treaty_ok},
            confidence=1.0 if qualified else 0.6,
            **_dated("1120-F", facts.tax_year),
        )


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-8833-TREATY", title="Treaty-based return position"
)
def rule_8833(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if not _is_foreign_corp(e) or not e.holds_us_partnership_interest:
            continue
        if not e.treaty_lob_qualified:
            continue
        yield RuleResult(
            rule_id="R-8833-TREATY",
            form="8833",
            entity_id=e.entity_id,
            requirement=Requirement.REQUIRED,
            rationale=(
                f"{e.name} relies on the Canada–U.S. treaty to reduce the branch profits "
                f"rate. Any treaty-based return position must be disclosed on Form 8833 "
                f"attached to the return; the penalty for omission is $1,000 per failure "
                f"for a corporation, and an undisclosed position is also weaker on audit."
            ),
            authority="IRC §6114; IRC §6712; Treas. Reg. §301.6114-1",
            triggering_facts={"treaty_country": e.treaty_country},
            **_dated("1120-F", facts.tax_year),
        )


# --------------------------------------------------------------------------------------
# Withholding — credits that must be reconciled before they can be claimed
# --------------------------------------------------------------------------------------
@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-1446-WITHHOLDING", title="§1446 ECTI withholding credit"
)
def rule_1446(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if e.withholding_1446 <= 0:
            continue
        yield RuleResult(
            rule_id="R-1446-WITHHOLDING",
            form="8805",
            entity_id=e.entity_id,
            requirement=Requirement.REQUIRED,
            rationale=(
                f"${e.withholding_1446:,.0f} of §1446 withholding was remitted on effectively "
                f"connected taxable income allocated to {e.name}. Each Form 8805 must be "
                f"matched to the corresponding K-1 box 15 code O and the payee TIN verified "
                f"against the filing entity before the credit is claimed on the 1120-F. A "
                f"mismatch between the 8805 payee and the filer is the most common reason "
                f"this credit is disallowed, and it is fixable only by the partnership."
            ),
            authority="IRC §1446; Treas. Reg. §1.1446-3; Forms 8804/8805/8813",
            triggering_facts={"withholding_1446": e.withholding_1446},
            **_dated("8805", facts.tax_year),
        )


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-FIRPTA-DISP", title="FIRPTA / USRPI disposition"
)
def rule_firpta(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if not (e.partnership_disposed_usrpi or e.usrpi_gain or e.withholding_1445):
            continue
        yield RuleResult(
            rule_id="R-FIRPTA-DISP",
            form="8288-A",
            entity_id=e.entity_id,
            requirement=Requirement.REQUIRED,
            rationale=(
                f"A U.S. real property interest was disposed of and ${e.usrpi_gain:,.0f} of "
                f"§897 gain flows through to {e.name}. The gain is treated as effectively "
                f"connected income and reported on the 1120-F; ${e.withholding_1445:,.0f} of "
                f"§1445 withholding is claimed as a credit against the resulting tax."
            ),
            authority="IRC §897; IRC §1445; Treas. Reg. §1.1445-5(c)",
            triggering_facts={
                "usrpi_gain": e.usrpi_gain,
                "withholding_1445": e.withholding_1445,
            },
            **_dated("1120-F", facts.tax_year),
        )


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-1446F-TRANSFER", title="§1446(f) interest transfer"
)
def rule_1446f(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if not e.disposed_partnership_interest:
            continue
        yield RuleResult(
            rule_id="R-1446F-TRANSFER",
            form="8288",
            entity_id=e.entity_id,
            requirement=Requirement.REQUIRED,
            rationale=(
                f"{e.name} transferred an interest in a partnership engaged in a U.S. trade "
                f"or business. §1446(f) obliges the transferee to withhold 10% of the amount "
                f"realised unless a certification applies; the transferor claims the credit "
                f"and reports the gain, which is ECI to the extent of §864(c)(8) deemed sale."
            ),
            authority="IRC §1446(f); IRC §864(c)(8); Treas. Reg. §1.1446(f)-2",
            triggering_facts={"disposed": True},
            **_dated("1120-F", facts.tax_year),
        )


# --------------------------------------------------------------------------------------
# International information returns
# --------------------------------------------------------------------------------------
@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-8865-CFP", title="Form 8865 — foreign partnership"
)
def rule_8865(facts: FactBase) -> Iterable[RuleResult]:
    """The engagement asks about 8865 by name, so answer it explicitly either way."""
    for e in facts.entities:
        if e.entity_type not in {"ca_partnership"}:
            # Evaluate once, at the level of each foreign corporate holder, and record the
            # negative determination so the client sees the question was asked.
            if _is_foreign_corp(e) and e.holds_us_partnership_interest:
                yield RuleResult(
                    rule_id="R-8865-CFP",
                    form="8865",
                    entity_id=e.entity_id,
                    requirement=Requirement.NOT_REQUIRED,
                    rationale=(
                        f"Form 8865 applies to a *U.S.* person holding an interest in a "
                        f"*foreign* partnership. {e.name} is a Canadian corporation holding "
                        f"interests in U.S. limited partnerships — the mirror image. No U.S. "
                        f"person sits above the structure, so no §6038 filing obligation "
                        f"arises here; the corresponding U.S.-side reporting is the "
                        f"partnerships' own Forms 1065 and their §1446 withholding. This "
                        f"determination is recorded rather than omitted so the position is "
                        f"visible in the file."
                    ),
                    authority="IRC §6038, §6038B, §6046A; Form 8865 instructions",
                    triggering_facts={"us_owner_above": e.us_owner_above},
                    **_dated("8865", facts.tax_year),
                )
            continue

        if e.us_owner_above:
            yield RuleResult(
                rule_id="R-8865-CFP",
                form="8865",
                entity_id=e.entity_id,
                requirement=Requirement.REQUIRED,
                rationale=(
                    f"A U.S. person holds a reportable interest in {e.name}, a foreign "
                    f"partnership. Category is determined by control and acquisition events; "
                    f"a Category 1 or 2 filer attaches full Schedules K/K-1 equivalents."
                ),
                authority="IRC §6038, §6038B, §6046A",
                triggering_facts={"us_owner_above": True},
                **_dated("8865", facts.tax_year),
            )


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-5472-REPORTABLE", title="25% foreign-owned U.S. entity"
)
def rule_5472(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        is_us_reporting_corp = e.entity_type in {"us_corporation", "us_disregarded"}
        if not is_us_reporting_corp:
            continue
        foreign_owners = [o for o in facts.owners_of(e.entity_id) if o.country != "US"]
        if not foreign_owners:
            continue
        yield RuleResult(
            rule_id="R-5472-REPORTABLE",
            form="5472",
            entity_id=e.entity_id,
            requirement=(
                Requirement.REQUIRED
                if e.has_reportable_related_party_transactions
                else Requirement.NEEDS_ANALYSIS
            ),
            rationale=(
                f"{e.name} is at least 25% foreign-owned. Form 5472 is required for each "
                f"reportable transaction with a related party; where the entity is a "
                f"disregarded entity it files a pro-forma Form 1120 with the 5472 attached. "
                f"The penalty is $25,000 per form per year, which makes this the highest "
                f"cost-per-page form in the structure."
            ),
            authority=(
                "IRC §6038A; Treas. Reg. §1.6038A-2; §301.7701-2(c)(2)(vi); IRC §6038A(d)"
            ),
            triggering_facts={
                "foreign_owners": [o.name for o in foreign_owners],
                "reportable_transactions": e.has_reportable_related_party_transactions,
            },
            confidence=1.0 if e.has_reportable_related_party_transactions else 0.55,
            **_dated("5472", facts.tax_year),
        )


# --------------------------------------------------------------------------------------
# Limitations and carryforwards
# --------------------------------------------------------------------------------------
@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-163J-EBIE", title="§163(j) excess business interest"
)
def rule_163j(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if e.excess_business_interest <= 0:
            continue
        yield RuleResult(
            rule_id="R-163J-EBIE",
            form="8990",
            entity_id=e.entity_id,
            requirement=Requirement.REQUIRED,
            rationale=(
                f"${e.excess_business_interest:,.0f} of excess business interest expense was "
                f"allocated to {e.name} (K-1 box 13 code K). EBIE is suspended at the partner "
                f"level and released only by excess taxable income from the *same* "
                f"partnership — it is tracked per partnership and never pooled across the "
                f"five syndications. A carryforward schedule is maintained per investment."
            ),
            authority="IRC §163(j); Treas. Reg. §1.163(j)-6",
            triggering_facts={"ebie": e.excess_business_interest},
            **_dated("1120-F", facts.tax_year),
        )


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-BASIS-LIMIT", title="Loss limitation stack"
)
def rule_basis_limits(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if e.allocated_loss >= 0:
            continue
        loss = abs(e.allocated_loss)
        limited_by_basis = loss > e.outside_basis
        limited_by_at_risk = loss > e.at_risk_amount
        yield RuleResult(
            rule_id="R-BASIS-LIMIT",
            form="Loss limitation workpaper",
            entity_id=e.entity_id,
            requirement=Requirement.REQUIRED,
            rationale=(
                f"${loss:,.0f} of allocated loss must run the limitation stack in order: "
                f"§704(d) outside basis (${e.outside_basis:,.0f}), then §465 at-risk "
                f"(${e.at_risk_amount:,.0f}, including ${e.qualified_nonrecourse_debt:,.0f} "
                f"of qualified nonrecourse financing that *is* at-risk under §465(b)(6)), "
                f"then §469 passive activity. "
                + (
                    "The loss is limited at an earlier step than §469, so the suspended "
                    "amount carries with that step's release condition, not the passive one."
                    if (limited_by_basis or limited_by_at_risk)
                    else "The loss clears basis and at-risk and is suspended as passive."
                )
            ),
            authority="IRC §704(d); IRC §465(b)(6); IRC §469; IRC §461(l)",
            triggering_facts={
                "loss": loss,
                "outside_basis": e.outside_basis,
                "at_risk": e.at_risk_amount,
                "limited_by_basis": limited_by_basis,
                "limited_by_at_risk": limited_by_at_risk,
            },
        )


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-EXTENSION", title="Extension of time to file"
)
def rule_extension(facts: FactBase) -> Iterable[RuleResult]:
    """Default posture: extend everything.

    Syndicator K-1s routinely arrive after the original due date. Extending is free;
    filing late is not.
    """
    for e in facts.entities:
        if not (_is_foreign_corp(e) and e.holds_us_partnership_interest):
            continue
        yield RuleResult(
            rule_id="R-EXTENSION",
            form="7004",
            entity_id=e.entity_id,
            requirement=Requirement.RECOMMENDED,
            rationale=(
                f"K-1s from the syndications for {e.name} historically arrive after the "
                f"original due date. Form 7004 extends the 1120-F from "
                f"{form_due_date('1120-F', facts.tax_year):%B %d, %Y} to "
                f"{extended_due_date('1120-F', facts.tax_year):%B %d, %Y}. Note the extension "
                f"is of time to file, not to pay — any §1446 credit shortfall still accrues "
                f"interest from the original date."
            ),
            authority="Treas. Reg. §1.6081-3; Form 7004 instructions",
            triggering_facts={"k1_count": e.k1_count},
            due_date=form_due_date("1120-F", facts.tax_year),
            extended_due_date=extended_due_date("1120-F", facts.tax_year),
        )


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-871D-ELECTION", title="§882(d) net basis election"
)
def rule_871d(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if not _is_foreign_corp(e) or not e.holds_us_partnership_interest:
            continue
        if e.eci_income or e.rental_income or e.ordinary_income:
            continue  # already net-basis through the partnership's trade or business
        yield RuleResult(
            rule_id="R-871D-ELECTION",
            form="§882(d) election statement",
            entity_id=e.entity_id,
            requirement=(
                Requirement.NOT_REQUIRED if e.net_election_871d else Requirement.NEEDS_ANALYSIS
            ),
            rationale=(
                f"{e.name} has U.S. real property income with no active trade or business "
                f"characterisation this year. A §882(d) election treats it as effectively "
                f"connected so deductions — depreciation above all — become available "
                f"against it instead of 30% gross withholding. "
                + (
                    "An election is already on file from a prior year and remains binding, so "
                    "no new statement is needed."
                    if e.net_election_871d
                    else "Once made the election binds all later years absent IRS consent to "
                    "revoke, so it is a decision to take deliberately rather than by default."
                )
            ),
            authority="IRC §882(d); IRC §871(d); Treas. Reg. §1.871-10",
            triggering_facts={"existing_election": e.net_election_871d},
            confidence=0.7,
        )
