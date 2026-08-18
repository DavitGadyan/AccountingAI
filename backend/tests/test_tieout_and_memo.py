"""Year-over-year comparison and the client memo.

The memo is a deliverable the client reads. It must be generated without a network call,
which is what this file proves.
"""

from __future__ import annotations

import pytest

from app.rules.engine import DeterminationEngine
from app.services import memo, tieout
from tests.fixtures import HOLDCO_A, build_fact_base


@pytest.fixture
def engine() -> DeterminationEngine:
    return DeterminationEngine(2025)


def test_snapshot_round_trips_into_a_comparison(engine):
    prior = tieout.snapshot(build_fact_base(tax_year=2024))
    current = build_fact_base(tax_year=2025)

    assert tieout.compare(current, prior) == []  # identical facts, no variance


def test_material_income_swing_is_flagged_with_an_explanation(engine):
    prior = tieout.snapshot(build_fact_base(tax_year=2024, holdco_a_rental=148_000.0))
    current = build_fact_base(tax_year=2025, holdco_a_rental=22_000.0)

    variances = [v for v in tieout.compare(current, prior) if v.entity_id == HOLDCO_A]
    rental = [v for v in variances if v.metric == "rental_income"]

    assert rental and rental[0].is_material
    assert "decreased" in rental[0].explanation


def test_immaterial_movement_is_not_flagged():
    prior = tieout.snapshot(build_fact_base(tax_year=2024, holdco_a_rental=148_000.0))
    current = build_fact_base(tax_year=2025, holdco_a_rental=148_900.0)

    assert not [
        v
        for v in tieout.compare(current, prior)
        if v.metric == "rental_income" and v.entity_id == HOLDCO_A
    ]


def test_a_missing_k1_shows_up_as_a_count_variance_with_both_readings():
    """Fewer K-1s means an exit or a late document. The memo must say both."""
    prior_facts = build_fact_base(tax_year=2024)
    prior = tieout.snapshot(prior_facts)
    prior[HOLDCO_A]["k1_count"] = 4

    variances = tieout.compare(build_fact_base(tax_year=2025), prior)
    count = [v for v in variances if v.metric == "k1_count" and v.entity_id == HOLDCO_A]

    assert count
    assert "exited" in count[0].explanation
    assert "has not arrived" in count[0].explanation


def test_withholding_variance_explains_the_usual_cause():
    prior = tieout.snapshot(build_fact_base(tax_year=2024, withholding_a=31_080.0))
    current = build_fact_base(tax_year=2025, withholding_a=4_000.0)

    wh = [
        v
        for v in tieout.compare(current, prior)
        if v.metric == "withholding_1446" and v.entity_id == HOLDCO_A
    ]
    assert wh
    assert "8805" in wh[0].explanation


def test_memo_is_generated_offline_and_covers_the_deliverables(engine):
    facts = build_fact_base()
    results = engine.run(facts)
    text = memo.build_memo(facts, results, [], "Northgate Investor Group")

    assert "# 2025 U.S. tax filing summary" in text
    assert "1120-F" in text
    assert "## State filings" in text
    assert "## Considered and not required" in text     # the 8865 answer
    assert "Canadian-side items" in text                # T1134 / T1135 / FTC
    assert "## For next year" in text


def test_memo_records_judgement_calls_separately_from_mechanics(engine):
    facts = build_fact_base(lob_qualified=None)
    results = engine.run(facts)
    text = memo.build_memo(facts, results, [], "Northgate Investor Group")

    assert "required a judgement call" in text
    assert "XXIX-A" in text


def test_memo_carries_authority_for_every_federal_position(engine):
    facts = build_fact_base()
    results = engine.run(facts)
    text = memo.build_memo(facts, results, [], "Client")

    assert text.count("*Authority:") >= 3
