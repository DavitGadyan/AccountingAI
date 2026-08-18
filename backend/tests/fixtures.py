"""The engagement from the job post, as a fact base.

Two Canadian holding companies, five U.S. multifamily syndications, K-1s with §1446
withholding, property in six states. Every test below runs against this shape because it
is the shape the platform was built for.
"""

from __future__ import annotations

from app.rules.base import EntityFacts, FactBase

HOLDCO_A = "holdco-a"
HOLDCO_B = "holdco-b"
LP_IDS = [f"lp-{i}" for i in range(1, 6)]


def syndication(lp_id: str, state: str) -> EntityFacts:
    return EntityFacts(
        entity_id=lp_id,
        name=f"{state} Multifamily Fund ({lp_id})",
        entity_type="us_partnership",
        tax_classification="partnership",
        country="US",
        formation_state="DE",
        is_syndication=True,
        property_states=(state,),
    )


def build_fact_base(
    *,
    tax_year: int = 2025,
    holdco_a_rental: float = 148_000.0,
    holdco_b_rental: float = -32_000.0,
    withholding_a: float = 31_080.0,
    withholding_b: float = 0.0,
    lob_qualified: bool | None = True,
    usrpi_gain: float = 0.0,
    k3_count_a: int = 3,
) -> FactBase:
    holdco_a = EntityFacts(
        entity_id=HOLDCO_A,
        name="Northgate Holdings Ltd.",
        entity_type="ca_corporation",
        tax_classification="foreign_corporation",
        country="CA",
        us_tin="98-7654321",
        treaty_country="CA",
        treaty_lob_qualified=lob_qualified,
        rental_income=holdco_a_rental,
        withholding_1446=withholding_a,
        usrpi_gain=usrpi_gain,
        excess_business_interest=18_400.0,
        outside_basis=612_000.0,
        at_risk_amount=612_000.0,
        qualified_nonrecourse_debt=340_000.0,
        holds_us_partnership_interest=True,
        partnership_disposed_usrpi=usrpi_gain > 0,
        property_states=("TX", "GA", "NC"),
        state_amounts={"TX": 61_000.0, "GA": 52_000.0, "NC": 35_000.0},
        k1_count=3,
        k3_count=k3_count_a,
    )
    holdco_b = EntityFacts(
        entity_id=HOLDCO_B,
        name="Bramalea Capital Corp.",
        entity_type="ca_corporation",
        tax_classification="foreign_corporation",
        country="CA",
        us_tin="98-1234567",
        treaty_country="CA",
        treaty_lob_qualified=lob_qualified,
        rental_income=holdco_b_rental,
        withholding_1446=withholding_b,
        allocated_loss=min(holdco_b_rental, 0.0),
        outside_basis=95_000.0,
        at_risk_amount=95_000.0 + 210_000.0,
        qualified_nonrecourse_debt=210_000.0,
        holds_us_partnership_interest=True,
        property_states=("AZ", "TN"),
        state_amounts={"AZ": -18_000.0, "TN": -14_000.0},
        k1_count=2,
        k3_count=2,
    )

    states = ["TX", "GA", "NC", "AZ", "TN"]
    lps = tuple(syndication(lp_id, state) for lp_id, state in zip(LP_IDS, states, strict=True))

    edges = tuple(
        (HOLDCO_A if i < 3 else HOLDCO_B, lp_id, 4.5) for i, lp_id in enumerate(LP_IDS)
    )

    return FactBase(
        tax_year=tax_year,
        engagement_id="eng-2025",
        entities=(holdco_a, holdco_b, *lps),
        ownership_edges=edges,
        ultimate_owner_country="CA",
    )
