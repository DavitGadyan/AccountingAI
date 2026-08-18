"""State determination tests.

The recurring failure in this work is not getting a state wrong — it is not looking at a
state at all. These tests assert that every situs state produces a recorded conclusion.
"""

from __future__ import annotations

import pytest

from app.models.enums import Requirement
from app.rules.engine import DeterminationEngine
from tests.fixtures import HOLDCO_A, HOLDCO_B, build_fact_base


@pytest.fixture
def engine() -> DeterminationEngine:
    return DeterminationEngine(2025)


def state_results(engine, facts, entity_id=None):
    out = [r for r in engine.run(facts) if r.jurisdiction == "us_state"]
    return [r for r in out if entity_id is None or r.entity_id == entity_id]


def test_every_property_state_gets_a_recorded_conclusion(engine):
    facts = build_fact_base()
    states_a = {r.state for r in state_results(engine, facts, HOLDCO_A)}
    states_b = {r.state for r in state_results(engine, facts, HOLDCO_B)}

    assert states_a == {"TX", "GA", "NC"}
    assert states_b == {"AZ", "TN"}


def test_texas_franchise_tax_is_not_skipped_for_having_no_income_tax(engine):
    facts = build_fact_base()
    tx = [r for r in state_results(engine, facts, HOLDCO_A) if r.state == "TX"]

    assert len(tx) == 1
    assert "franchise" in tx[0].rationale.lower()
    assert tx[0].requirement is not Requirement.NOT_REQUIRED


def test_tennessee_franchise_and_excise_is_caught(engine):
    """TN F&E reaches LPs directly and is the most commonly missed filing here."""
    facts = build_fact_base()
    tn = [r for r in state_results(engine, facts, HOLDCO_B) if r.state == "TN"]

    assert len(tn) == 1
    assert "67-4" in tn[0].authority


def test_below_threshold_states_record_a_negative_conclusion(engine):
    """A state examined and concluded not to require a return is still a deliverable."""
    facts = build_fact_base()
    facts_low = facts.__class__(
        tax_year=facts.tax_year,
        engagement_id=facts.engagement_id,
        entities=tuple(
            e.__class__(
                **{
                    **e.__dict__,
                    "state_amounts": {"GA": 400.0},
                    "property_states": ("GA",),
                }
            )
            if e.entity_id == HOLDCO_A
            else e
            for e in facts.entities
        ),
        ownership_edges=facts.ownership_edges,
    )
    ga = [r for r in state_results(engine, facts_low, HOLDCO_A) if r.state == "GA"]

    assert len(ga) == 1
    assert ga[0].requirement is Requirement.NOT_REQUIRED
    assert "threshold" in ga[0].rationale


def test_composite_election_surfaces_a_choice_rather_than_a_default(engine):
    facts = build_fact_base()
    entities = tuple(
        e.__class__(**{**e.__dict__, "composite_states": ("GA",)})
        if e.entity_id == HOLDCO_A
        else e
        for e in facts.entities
    )
    facts = facts.__class__(
        tax_year=facts.tax_year,
        engagement_id=facts.engagement_id,
        entities=entities,
        ownership_edges=facts.ownership_edges,
    )
    ga = [r for r in state_results(engine, facts, HOLDCO_A) if r.state == "GA"]

    assert ga[0].rule_id == "R-STATE-COMPOSITE"
    assert ga[0].requirement is Requirement.NEEDS_ANALYSIS
    assert "top marginal rate" in ga[0].rationale


def test_unknown_state_is_flagged_for_research_not_guessed(engine):
    facts = build_fact_base()
    entities = tuple(
        e.__class__(
            **{**e.__dict__, "property_states": ("WY",), "state_amounts": {"WY": 20_000.0}}
        )
        if e.entity_id == HOLDCO_A
        else e
        for e in facts.entities
    )
    facts = facts.__class__(
        tax_year=facts.tax_year,
        engagement_id=facts.engagement_id,
        entities=entities,
        ownership_edges=facts.ownership_edges,
    )
    wy = [r for r in state_results(engine, facts, HOLDCO_A) if r.state == "WY"]

    assert wy[0].requirement is Requirement.NEEDS_ANALYSIS
    assert wy[0].confidence < 0.5
