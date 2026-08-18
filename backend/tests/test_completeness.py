"""Open items must be found in March, not in November."""

from __future__ import annotations

import pytest

from app.models.enums import IssueSeverity
from app.rules.engine import DeterminationEngine
from app.services import completeness
from tests.fixtures import HOLDCO_A, build_fact_base


@pytest.fixture
def engine() -> DeterminationEngine:
    return DeterminationEngine(2025)


def detect(engine, facts, expected=None):
    return completeness.detect(facts, engine.run(facts), expected or {})


def codes(items):
    return {i.code for i in items}


def test_missing_k1_blocks_filing(engine):
    facts = build_fact_base()
    items = detect(engine, facts, {HOLDCO_A: 5})  # 5 expected, 3 received

    missing = [i for i in items if i.code == "MISSING_K1"]
    assert len(missing) == 1
    assert missing[0].blocks_filing is True
    assert missing[0].severity is IssueSeverity.BLOCKING
    assert missing[0].requested_from == "syndicator"


def test_missing_k3_blocks_filing(engine):
    facts = build_fact_base(k3_count_a=1)
    items = detect(engine, facts)

    k3 = [i for i in items if i.code == "MISSING_K3" and i.entity_id == HOLDCO_A]
    assert len(k3) == 1
    assert k3[0].blocks_filing is True


def test_complete_document_set_produces_no_missing_document_items(engine):
    facts = build_fact_base(k3_count_a=3)
    items = detect(engine, facts, {HOLDCO_A: 3})

    assert "MISSING_K1" not in codes([i for i in items if i.entity_id == HOLDCO_A])
    assert "MISSING_K3" not in codes([i for i in items if i.entity_id == HOLDCO_A])


def test_undocumented_lob_analysis_is_raised_before_the_rate_is_claimed(engine):
    facts = build_fact_base(lob_qualified=None)
    items = detect(engine, facts)

    lob = [i for i in items if i.code == "LOB_UNDOCUMENTED"]
    assert lob
    assert "30%" in lob[0].detail


def test_documented_lob_produces_no_open_item(engine):
    facts = build_fact_base(lob_qualified=True)
    assert not [i for i in detect(engine, facts) if i.code == "LOB_UNDOCUMENTED"]


def test_needs_analysis_determinations_become_open_items(engine):
    facts = build_fact_base(lob_qualified=None)
    items = detect(engine, facts)

    assert any(i.code.startswith("ANALYSIS_") for i in items)


def test_capital_account_is_not_mistaken_for_outside_basis(engine):
    """Item L capital is not §704(d) basis. Treating them as equal is a real-world error."""
    facts = build_fact_base()
    entities = tuple(
        e.__class__(**{**e.__dict__, "outside_basis": 0.0}) if e.entity_id == HOLDCO_A else e
        for e in facts.entities
    )
    facts = facts.__class__(
        tax_year=facts.tax_year,
        engagement_id=facts.engagement_id,
        entities=entities,
        ownership_edges=facts.ownership_edges,
    )
    items = detect(engine, facts)

    basis = [i for i in items if i.code == "BASIS_UNKNOWN"]
    assert basis
    assert "not outside basis" in basis[0].detail
