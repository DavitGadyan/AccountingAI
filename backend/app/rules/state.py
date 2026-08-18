"""State determination rules.

Nexus follows the *property*, not the partnership's formation state. A Delaware LP that
owns an apartment complex in Georgia creates a Georgia obligation and no Delaware one.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.models.enums import Requirement
from app.rules.base import SUPPORTED_YEARS, FactBase, RuleResult, registry
from app.rules.calendar import state_due_date

# Filing threshold and mechanism per state, for the states multifamily deals concentrate in.
STATE_PROFILE: dict[str, dict] = {
    "TX": {
        "income_tax": False,
        "form": "TX 05-158 Franchise Report",
        "mechanism": "franchise (margin) tax",
        "no_tax_due_threshold": 2_470_000.0,
        "authority": "Tex. Tax Code §171.001, §171.002; Comptroller Rule 3.586",
        "note": (
            "Texas has no income tax, which is why it gets skipped. It does have a margin "
            "tax with an entity-level nexus test, and a non-U.S. entity holding a "
            "Texas-situs partnership interest can fall inside it."
        ),
    },
    "FL": {
        "income_tax": True,
        "form": "F-1120",
        "mechanism": "corporate income tax",
        "threshold": 0.0,
        "authority": "Fla. Stat. §220.11, §220.13",
        "note": (
            "No individual income tax, but the corporate income tax reaches a foreign "
            "corporation with Florida-apportioned ECI."
        ),
    },
    "GA": {
        "income_tax": True,
        "form": "GA 600 / composite",
        "mechanism": "nonresident withholding or composite",
        "threshold": 1_000.0,
        "withholding_rate": 0.04,
        "authority": "O.C.G.A. §48-7-129",
    },
    "NC": {
        "income_tax": True,
        "form": "NC D-403 partner filing / composite",
        "mechanism": "nonresident withholding or composite",
        "threshold": 0.0,
        "withholding_rate": 0.045,
        "authority": "N.C.G.S. §105-154(d)",
    },
    "AZ": {
        "income_tax": True,
        "form": "AZ 140NR / 120",
        "mechanism": "nonresident composite available",
        "threshold": 0.0,
        "authority": "A.R.S. §43-1097, §43-1014",
    },
    "TN": {
        "income_tax": True,
        "form": "TN FAE 170",
        "mechanism": "franchise & excise tax",
        "threshold": 0.0,
        "authority": "Tenn. Code Ann. §67-4-2007, §67-4-2105",
        "note": (
            "Tennessee F&E reaches limited partnerships directly and is the single most "
            "commonly missed state filing in multifamily syndication portfolios."
        ),
    },
    "OH": {
        "income_tax": True,
        "form": "OH IT 4708 / IT 1140",
        "mechanism": "pass-through entity withholding or composite",
        "threshold": 0.0,
        "withholding_rate": 0.05,
        "authority": "Ohio Rev. Code §5733.40, §5747.08",
    },
}


@registry.register(
    years=SUPPORTED_YEARS, rule_id="R-STATE-NEXUS", title="State filing obligation by situs"
)
def rule_state_nexus(facts: FactBase) -> Iterable[RuleResult]:
    for e in facts.entities:
        if not e.holds_us_partnership_interest:
            continue

        for state in e.property_states:
            profile = STATE_PROFILE.get(state)
            amount = float(e.state_amounts.get(state, 0.0))
            composite = state in e.composite_states

            if profile is None:
                yield RuleResult(
                    rule_id="R-STATE-NEXUS",
                    form=f"{state} return",
                    entity_id=e.entity_id,
                    jurisdiction="us_state",
                    state=state,
                    requirement=Requirement.NEEDS_ANALYSIS,
                    rationale=(
                        f"{e.name} has property-situs income in {state}, which is outside the "
                        f"engine's profiled states. Filing mechanism and threshold need "
                        f"manual research before this return is prepared."
                    ),
                    authority=f"{state} nonresident filing rules — research required",
                    triggering_facts={"state_income": amount},
                    confidence=0.3,
                    due_date=state_due_date(state, facts.tax_year),
                )
                continue

            if not profile["income_tax"]:
                over = amount > profile.get("no_tax_due_threshold", 0.0)
                yield RuleResult(
                    rule_id="R-STATE-NEXUS",
                    form=profile["form"],
                    entity_id=e.entity_id,
                    jurisdiction="us_state",
                    state=state,
                    requirement=Requirement.REQUIRED if over else Requirement.RECOMMENDED,
                    rationale=(
                        f"{state} imposes no income tax but does impose a "
                        f"{profile['mechanism']}. {e.name}'s {state} revenue of "
                        f"${amount:,.0f} is "
                        + ("above" if over else "below")
                        + " the no-tax-due threshold, so a report is "
                        + ("required with tax due" if over else "filed showing no tax due")
                        + f". {profile.get('note', '')}"
                    ),
                    authority=profile["authority"],
                    triggering_facts={"state_income": amount, "composite": composite},
                    due_date=state_due_date(state, facts.tax_year),
                )
                continue

            if composite:
                yield RuleResult(
                    rule_id="R-STATE-COMPOSITE",
                    form=profile["form"],
                    entity_id=e.entity_id,
                    jurisdiction="us_state",
                    state=state,
                    requirement=Requirement.NEEDS_ANALYSIS,
                    rationale=(
                        f"The syndicator made a composite election in {state} covering "
                        f"{e.name}'s ${amount:,.0f} of {state} income. A composite filing "
                        f"usually relieves the partner of a separate return — but it applies "
                        f"the top marginal rate with no personal exemptions and no ability to "
                        f"use {state} credits or other-activity losses. Both outcomes are "
                        f"computed in the state workpaper so the choice is made on numbers, "
                        f"not on whichever one the syndicator defaulted to."
                    ),
                    authority=profile["authority"],
                    triggering_facts={"state_income": amount, "composite_election": True},
                    confidence=0.75,
                    due_date=state_due_date(state, facts.tax_year),
                )
                continue

            required = amount > profile.get("threshold", 0.0)
            yield RuleResult(
                rule_id="R-STATE-NEXUS",
                form=profile["form"],
                entity_id=e.entity_id,
                jurisdiction="us_state",
                state=state,
                requirement=Requirement.REQUIRED if required else Requirement.NOT_REQUIRED,
                rationale=(
                    f"{e.name} is allocated ${amount:,.0f} of {state}-source income from "
                    f"property situated in {state}. {state} applies "
                    f"{profile['mechanism']}"
                    + (
                        f" at {profile['withholding_rate']:.1%}"
                        if profile.get("withholding_rate")
                        else ""
                    )
                    + (
                        "; the amount exceeds the filing threshold."
                        if required
                        else f"; the amount is below the ${profile.get('threshold', 0):,.0f} "
                        "filing threshold, so no return is due. Recorded so the conclusion is "
                        "visible next year when the number may cross it."
                    )
                ),
                authority=profile["authority"],
                triggering_facts={"state_income": amount, "threshold": profile.get("threshold")},
                due_date=state_due_date(state, facts.tax_year),
            )
