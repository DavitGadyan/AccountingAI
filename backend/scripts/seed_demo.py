"""Seed the engagement from the job post.

Two Canadian holdcos, five U.S. multifamily syndications across six states, K-1s with
§1446 withholding, and a prior year to tie out against. Run against a scratch database:

    AAI_DATABASE_URL=postgresql+asyncpg://... python scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio
from datetime import date

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import (
    Client,
    Engagement,
    Entity,
    Firm,
    K1Record,
    Ownership,
    PropertyState,
    User,
)
from app.models.enums import EntityType, TaxClassification, UserRole

SYNDICATIONS = [
    ("Sunbelt Apartment Fund III, LP", "TX", "Sunbelt Capital", 148_000, 31_080, 3.8),
    ("Peachtree Multifamily Partners II, LP", "GA", "Peachtree RE", 52_000, 10_920, 4.1),
    ("Carolina Residential Growth Fund, LP", "NC", "Carolina Yield", 35_000, 7_350, 5.0),
    ("Desert Ridge Apartment Investors, LP", "AZ", "Desert Ridge GP", -18_000, 0, 4.4),
    ("Volunteer State Housing Partners, LP", "TN", "Volunteer Capital", -14_000, 0, 6.2),
]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        firm = Firm(name="Cross-Border Tax Partners LLP", efin="123456", ptin="P01234567")
        session.add(firm)
        await session.flush()

        reviewer = User(
            firm_id=firm.id,
            email="dana.reyes@crossbordertax.test",
            full_name="Dana Reyes",
            hashed_password=hash_password("demo-password"),
            role=UserRole.REVIEWER,
            credential="CPA",
            credential_number="NY-118422",
            credential_state="NY",
        )
        preparer = User(
            firm_id=firm.id,
            email="sam.oyelaran@crossbordertax.test",
            full_name="Sam Oyelaran",
            hashed_password=hash_password("demo-password"),
            role=UserRole.PREPARER,
        )
        session.add_all([reviewer, preparer])
        await session.flush()

        client = Client(
            firm_id=firm.id,
            display_name="Northgate Investor Group",
            primary_contact_email="investor@northgate.test",
            residence_country="CA",
            notes=(
                "Canadian investor, passive LP positions in five U.S. multifamily "
                "syndications held through two Ontario holding companies."
            ),
        )
        session.add(client)
        await session.flush()

        holdco_a = Entity(
            firm_id=firm.id,
            client_id=client.id,
            name="Northgate Holdings Ltd.",
            entity_type=EntityType.CA_CORPORATION,
            tax_classification=TaxClassification.FOREIGN_CORPORATION,
            country="CA",
            us_tin="98-7654321",
            foreign_tin="BN 812345678",
            treaty_country="CA",
            treaty_lob_qualified=True,
            treaty_lob_basis=(
                "Qualifying person under Art. XXIX-A(2)(d) — shares of the ultimate "
                "Canadian-resident owner; ownership/base-erosion test documented in the "
                "2024 workpapers."
            ),
        )
        holdco_b = Entity(
            firm_id=firm.id,
            client_id=client.id,
            name="Bramalea Capital Corp.",
            entity_type=EntityType.CA_CORPORATION,
            tax_classification=TaxClassification.FOREIGN_CORPORATION,
            country="CA",
            us_tin="98-1234567",
            treaty_country="CA",
            treaty_lob_qualified=None,  # deliberately undocumented -> raises an open item
        )
        session.add_all([holdco_a, holdco_b])
        await session.flush()

        lps: list[Entity] = []
        for i, (name, _state, syndicator, _income, _wh, _pct) in enumerate(SYNDICATIONS):
            lp = Entity(
                firm_id=firm.id,
                client_id=client.id,
                name=name,
                entity_type=EntityType.US_PARTNERSHIP,
                tax_classification=TaxClassification.PARTNERSHIP,
                country="US",
                formation_state="DE",
                us_tin=f"87-{1000000 + i}",
                is_syndication=True,
                syndicator_name=syndicator,
                first_investment_date=date(2021 + (i % 3), 6, 1),
            )
            session.add(lp)
            lps.append(lp)
        await session.flush()

        for i, lp in enumerate(lps):
            owner = holdco_a if i < 3 else holdco_b
            pct = SYNDICATIONS[i][5]
            session.add(
                Ownership(
                    firm_id=firm.id,
                    owner_entity_id=owner.id,
                    owned_entity_id=lp.id,
                    profits_pct=pct,
                    capital_pct=pct,
                    effective_from=date(2021 + (i % 3), 6, 1),
                )
            )
            session.add(
                PropertyState(
                    firm_id=firm.id,
                    entity_id=lp.id,
                    state=SYNDICATIONS[i][1],
                    property_name=f"{SYNDICATIONS[i][1]} garden-style apartments",
                    apportionment_pct=100.0,
                    # The Georgia syndicator made a composite election without asking —
                    # the engine surfaces it as a decision rather than accepting it.
                    composite_election_made=SYNDICATIONS[i][1] == "GA",
                )
            )

        for tax_year in (2024, 2025):
            engagement = Engagement(
                firm_id=firm.id,
                client_id=client.id,
                tax_year=tax_year,
                fixed_fee=4_800 if tax_year == 2024 else 3_200,
                is_first_year=tax_year == 2024,
                assigned_preparer_id=preparer.id,
                assigned_reviewer_id=reviewer.id,
            )
            session.add(engagement)
            await session.flush()

            for i, lp in enumerate(lps):
                name, state, _s, income, wh, pct = SYNDICATIONS[i]
                owner = holdco_a if i < 3 else holdco_b
                # Prior year runs ~12% lower, which gives the tie-out something real to
                # compare against rather than an artificial zero baseline.
                scale = 0.88 if tax_year == 2024 else 1.0
                session.add(
                    K1Record(
                        firm_id=firm.id,
                        engagement_id=engagement.id,
                        document_id="seed",
                        partnership_entity_id=lp.id,
                        partner_entity_id=owner.id,
                        tax_year=tax_year,
                        form_year=tax_year,
                        partnership_ein=lp.us_tin,
                        partner_is_foreign=True,
                        boxes={
                            "box_2": round(income * scale, 2),
                            "box_5": round(1_200 * scale, 2),
                            "box_13_K": round(-6_100 * scale, 2) if i < 3 else 0,
                            "box_15_O": round(wh * scale, 2),
                            "box_19_A": round(max(income, 0) * 0.6 * scale, 2),
                        },
                        capital_account={
                            "beginning_capital": 200_000 + i * 15_000,
                            "current_year_net": round(income * scale, 2),
                            "withdrawals": round(max(income, 0) * 0.6 * scale, 2),
                            "ending_capital": 204_000 + i * 15_000,
                        },
                        liabilities={
                            "qualified_nonrecourse": 110_000 + i * 12_000,
                            "recourse": 0,
                        },
                        k3={"part_ii": {"us_source": round(income * scale, 2)}},
                        state_amounts={state: round(income * scale, 2)},
                        withholding_1446=round(wh * scale, 2),
                    )
                )

        await session.commit()

    print("Seeded: 1 firm, 2 users, 1 client, 7 entities, 5 syndications, 2 engagements")
    print("Login: dana.reyes@crossbordertax.test / demo-password  (CPA, reviewer)")


if __name__ == "__main__":
    asyncio.run(seed())
