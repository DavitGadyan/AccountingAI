"""Workpapers must tie out, and must say so when they do not."""

from __future__ import annotations

import pytest

from app.rules.engine import DeterminationEngine
from app.services import workpapers
from tests.fixtures import HOLDCO_A, HOLDCO_B, build_fact_base


@pytest.fixture
def engine() -> DeterminationEngine:
    return DeterminationEngine(2025)


def wp(drafts, code, entity_id=None):
    found = [
        d
        for d in drafts
        if d.code == code and (entity_id is None or d.entity_id == entity_id)
    ]
    return found[0] if found else None


def generate(engine, facts):
    results = engine.run(facts)
    return workpapers.generate_all(facts, results, engine.coverage())


def test_missing_k3_makes_the_k1_summary_fail_tie_out(engine):
    facts = build_fact_base(k3_count_a=1)
    summary = wp(generate(engine, facts), "WP-K1", HOLDCO_A)

    assert summary.ties_out is False
    assert "K-3" in summary.narrative


def test_complete_k3s_tie_out(engine):
    facts = build_fact_base(k3_count_a=3)
    summary = wp(generate(engine, facts), "WP-K1", HOLDCO_A)

    assert summary.ties_out is True


def test_1446_reconciliation_flags_a_withholding_mismatch(engine):
    """Expected withholding at 21% of $148k is ~$31k. A $9k figure must not pass."""
    facts = build_fact_base(withholding_a=9_000.0)
    recon = wp(generate(engine, facts), "WP-1446", HOLDCO_A)

    assert recon.ties_out is False
    assert "wrong tier" in recon.narrative


def test_1446_reconciliation_accepts_a_correct_figure(engine):
    facts = build_fact_base(holdco_a_rental=148_000.0, withholding_a=31_080.0)
    recon = wp(generate(engine, facts), "WP-1446", HOLDCO_A)

    assert recon.ties_out is True
    assert abs(recon.totals["difference"]) < 500


def test_basis_workpaper_applies_limitations_in_order(engine):
    facts = build_fact_base(holdco_b_rental=-32_000.0)
    basis = wp(generate(engine, facts), "WP-BASIS", HOLDCO_B)

    lines = [row["line"] for row in basis.rows]
    assert lines.index("Loss allowed after §704(d)") < lines.index("Loss allowed after §465")
    assert basis.totals["allowed"] == 32_000.0
    assert basis.totals["suspended_704d"] == 0.0


def test_basis_workpaper_suspends_loss_that_exceeds_basis(engine):
    facts = build_fact_base(holdco_b_rental=-500_000.0)
    basis = wp(generate(engine, facts), "WP-BASIS", HOLDCO_B)

    assert basis.totals["suspended_704d"] > 0
    assert basis.totals["allowed"] < 500_000.0


def test_state_matrix_lists_every_state_examined_including_negatives(engine):
    facts = build_fact_base()
    matrix = wp(generate(engine, facts), "WP-STATE", HOLDCO_A)

    assert matrix.totals["states_examined"] == 3
    assert all(row["authority"] for row in matrix.rows)


def test_determination_index_covers_every_registered_rule(engine):
    facts = build_fact_base()
    index = wp(generate(engine, facts), "WP-INDEX")

    assert index.totals["rules_evaluated"] == engine.rule_count
    assert len(index.rows) == engine.rule_count
    assert index.totals["not_required"] >= 1  # the 8865 conclusion


def test_every_workpaper_carries_a_narrative(engine):
    facts = build_fact_base()
    for draft in generate(engine, facts):
        assert draft.narrative.strip(), f"{draft.code} has no narrative"
        assert len(draft.narrative) > 80, f"{draft.code} narrative is filler"
