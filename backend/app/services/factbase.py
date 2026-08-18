"""Turns database rows into the immutable fact base the rules engine reads.

This is the only place that knows how a K-1 box maps onto a rule input. Keeping that
mapping in one function means a form change is a one-file edit, and it means the rules
never touch the ORM.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Engagement, Entity, K1Record, Ownership, PropertyState
from app.rules.base import EntityFacts, FactBase

# K-1 (Form 1065) Part III box -> rule input. Codes follow the 2024/2025 form.
BOX_ORDINARY = "box_1"           # ordinary business income (loss)
BOX_RENTAL_RE = "box_2"          # net rental real estate income (loss) - the main one here
BOX_OTHER_RENTAL = "box_3"
BOX_INTEREST = "box_5"
BOX_DIVIDENDS = "box_6a"
BOX_1231 = "box_10"
BOX_CAPITAL_LT = "box_9a"
BOX_EBIE = "box_13_K"            # excess business interest expense
BOX_1446_WH = "box_15_O"         # credit for section 1446 withholding
BOX_897_GAIN = "box_20_AH"       # section 897 / USRPI information


def _sum_boxes(records: list[K1Record], key: str) -> float:
    return sum(r.box(key) for r in records)


async def build_fact_base(session: AsyncSession, engagement_id: str) -> FactBase:
    engagement = await session.get(Engagement, engagement_id)
    if engagement is None:
        raise ValueError(f"Engagement {engagement_id} not found")

    entities = list(
        await session.scalars(select(Entity).where(Entity.client_id == engagement.client_id))
    )
    entity_ids = {e.id for e in entities}

    edges = list(
        await session.scalars(select(Ownership).where(Ownership.owner_entity_id.in_(entity_ids)))
    )
    k1s = list(
        await session.scalars(select(K1Record).where(K1Record.engagement_id == engagement_id))
    )
    states = list(
        await session.scalars(select(PropertyState).where(PropertyState.entity_id.in_(entity_ids)))
    )

    return assemble(engagement.tax_year, engagement_id, entities, edges, k1s, states)


def assemble(
    tax_year: int,
    engagement_id: str,
    entities: list[Entity],
    edges: list[Ownership],
    k1s: list[K1Record],
    states: list[PropertyState],
) -> FactBase:
    """Pure assembly step, separated from I/O so it is directly testable."""

    # A K-1 is issued *by* a partnership *to* a partner. Rules are written from the
    # partner's point of view, so index by partner.
    by_partner: dict[str, list[K1Record]] = defaultdict(list)
    for k1 in k1s:
        by_partner[k1.partner_entity_id].append(k1)

    states_by_entity: dict[str, list[PropertyState]] = defaultdict(list)
    for ps in states:
        states_by_entity[ps.entity_id].append(ps)

    owned_by: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        owned_by[edge.owner_entity_id].add(edge.owned_entity_id)

    entity_index = {e.id: e for e in entities}
    facts: list[EntityFacts] = []

    for e in entities:
        records = by_partner.get(e.id, [])
        holdings = owned_by.get(e.id, set())

        # Roll property states up from each partnership held.
        prop_states: list[str] = []
        composite_states: list[str] = []
        state_amounts: dict[str, float] = defaultdict(float)
        for held_id in holdings:
            for ps in states_by_entity.get(held_id, []):
                prop_states.append(ps.state)
                if ps.composite_election_made:
                    composite_states.append(ps.state)
        for r in records:
            for st, amount in (r.state_amounts or {}).items():
                try:
                    state_amounts[st] += float(amount)
                except (TypeError, ValueError):
                    continue
                if st not in prop_states:
                    prop_states.append(st)

        rental = _sum_boxes(records, BOX_RENTAL_RE) + _sum_boxes(records, BOX_OTHER_RENTAL)
        ordinary = _sum_boxes(records, BOX_ORDINARY)
        interest_div = _sum_boxes(records, BOX_INTEREST) + _sum_boxes(records, BOX_DIVIDENDS)
        usrpi = _sum_boxes(records, BOX_897_GAIN)
        cap_gain = _sum_boxes(records, BOX_CAPITAL_LT) + _sum_boxes(records, BOX_1231)
        ebie = abs(_sum_boxes(records, BOX_EBIE))
        wh_1446 = sum(float(r.withholding_1446 or 0) for r in records) or _sum_boxes(
            records, BOX_1446_WH
        )

        allocated = rental + ordinary
        outside_basis = sum(
            float((r.capital_account or {}).get("ending_capital", 0) or 0) for r in records
        )
        qnr = sum(
            float((r.liabilities or {}).get("qualified_nonrecourse", 0) or 0) for r in records
        )

        holds_us_lp = any(
            (held := entity_index.get(h)) is not None
            and held.country == "US"
            and str(held.entity_type) in {"us_partnership", "us_llc"}
            for h in holdings
        )

        facts.append(
            EntityFacts(
                entity_id=e.id,
                name=e.name,
                entity_type=str(e.entity_type),
                tax_classification=str(e.tax_classification),
                country=e.country,
                formation_state=e.formation_state,
                us_tin=e.us_tin,
                treaty_country=e.treaty_country,
                treaty_lob_qualified=e.treaty_lob_qualified,
                net_election_871d=bool(e.net_election_871d),
                is_syndication=bool(e.is_syndication),
                exited=e.exited_on is not None,
                fdap_income=interest_div,
                rental_income=rental,
                ordinary_income=ordinary,
                capital_gain=cap_gain,
                usrpi_gain=usrpi,
                withholding_1446=wh_1446,
                excess_business_interest=ebie,
                allocated_loss=min(allocated, 0.0),
                outside_basis=outside_basis,
                # At-risk includes qualified nonrecourse financing (section 465(b)(6)) -
                # the distinction that makes real-estate at-risk different from every
                # other activity.
                at_risk_amount=outside_basis + qnr,
                qualified_nonrecourse_debt=qnr,
                holds_us_partnership_interest=holds_us_lp,
                partnership_disposed_usrpi=usrpi > 0,
                property_states=tuple(dict.fromkeys(prop_states)),
                composite_states=tuple(dict.fromkeys(composite_states)),
                state_amounts=dict(state_amounts),
                k1_count=len(records),
                k3_count=sum(1 for r in records if r.k3),
            )
        )

    return FactBase(
        tax_year=tax_year,
        engagement_id=engagement_id,
        entities=tuple(facts),
        ownership_edges=tuple(
            (e.owner_entity_id, e.owned_entity_id, float(e.profits_pct)) for e in edges
        ),
        ultimate_owner_country="CA",
    )
