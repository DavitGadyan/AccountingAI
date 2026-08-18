"""Canadian advisory flags are raised, and are clearly labelled as out of scope."""

from __future__ import annotations

import pytest

from app.rules.engine import DeterminationEngine
from tests.fixtures import build_fact_base


@pytest.fixture
def engine() -> DeterminationEngine:
    return DeterminationEngine(2025)


def test_canadian_holdcos_get_t1134_and_t1135_flags(engine):
    facts = build_fact_base()
    ca = [r for r in engine.run(facts) if r.jurisdiction == "canada_federal"]
    forms = {r.form for r in ca}

    assert "T1134 (advisory)" in forms
    assert "T1135 (advisory)" in forms


def test_advisory_flags_say_they_are_not_prepared_here(engine):
    facts = build_fact_base()
    ca = [r for r in engine.run(facts) if r.jurisdiction == "canada_federal"]

    for r in ca:
        assert "advisory" in r.form.lower() or "advisory" in r.rationale.lower()


def test_foreign_tax_credit_coordination_is_raised_when_us_tax_was_paid(engine):
    facts = build_fact_base(withholding_a=31_080.0)
    ftc = [r for r in engine.run(facts) if r.rule_id == "R-CA-FTC"]

    assert len(ftc) == 1
    assert "creditable in Canada" in ftc[0].rationale


def test_no_ftc_flag_when_no_us_tax_was_paid(engine):
    facts = build_fact_base(withholding_a=0.0, withholding_b=0.0)
    assert [r for r in engine.run(facts) if r.rule_id == "R-CA-FTC"] == []
