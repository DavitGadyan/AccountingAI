"""Federal determination tests.

These assert *conclusions*, not code paths. A rule that fires with the wrong requirement
is worse than one that does not fire at all, because it looks like it worked.
"""

from __future__ import annotations

import pytest

from app.models.enums import Requirement
from app.rules.engine import DeterminationEngine
from tests.fixtures import HOLDCO_A, HOLDCO_B, build_fact_base


@pytest.fixture
def engine() -> DeterminationEngine:
    return DeterminationEngine(2025)


def results_for(engine, facts, entity_id=None, form=None, rule_id=None):
    out = engine.run(facts)
    if entity_id:
        out = [r for r in out if r.entity_id == entity_id]
    if form:
        out = [r for r in out if r.form == form]
    if rule_id:
        out = [r for r in out if r.rule_id == rule_id]
    return out


def test_canadian_holdco_with_eci_requires_1120f(engine):
    facts = build_fact_base()
    found = results_for(engine, facts, entity_id=HOLDCO_A, form="1120-F", rule_id="R-1120F-ECI")

    assert len(found) == 1
    assert found[0].requirement is Requirement.REQUIRED
    assert "875(1)" in found[0].authority
    assert "effectively connected" in found[0].rationale


def test_holdco_without_eci_gets_protective_return_not_silence(engine):
    """No ECI is not the same as no filing. §882(c)(2) is why."""
    facts = build_fact_base(holdco_a_rental=0.0, withholding_a=0.0)
    found = results_for(engine, facts, entity_id=HOLDCO_A, form="1120-F")

    protective = [r for r in found if r.requirement is Requirement.PROTECTIVE]
    assert len(protective) == 1
    assert "1.882-4(a)(3)(vi)" in protective[0].authority
    assert "882(c)(2)" in protective[0].rationale or "882(c)(2)" in protective[0].authority


def test_1120f_due_date_is_sixth_month_for_foreign_corp(engine):
    """June 15, not April 15. The single most commonly mis-diarised date in this work."""
    facts = build_fact_base()
    found = results_for(engine, facts, entity_id=HOLDCO_A, rule_id="R-1120F-ECI")[0]

    assert found.due_date.month == 6
    assert found.due_date.year == 2026
    assert found.extended_due_date.month == 12


def test_branch_profits_needs_lob_analysis_before_treaty_rate(engine):
    facts = build_fact_base(lob_qualified=None)
    found = results_for(engine, facts, entity_id=HOLDCO_A, rule_id="R-BRANCH-PROFITS")

    assert len(found) == 1
    assert found[0].requirement is Requirement.NEEDS_ANALYSIS
    assert "XXIX-A" in found[0].authority
    assert found[0].confidence < 1.0


def test_branch_profits_claims_five_percent_when_lob_documented(engine):
    facts = build_fact_base(lob_qualified=True)
    found = results_for(engine, facts, entity_id=HOLDCO_A, rule_id="R-BRANCH-PROFITS")[0]

    assert found.requirement is Requirement.REQUIRED
    assert "5%" in found.rationale


def test_treaty_position_triggers_8833_disclosure(engine):
    facts = build_fact_base(lob_qualified=True)
    found = results_for(engine, facts, entity_id=HOLDCO_A, form="8833")

    assert len(found) == 1
    assert "6114" in found[0].authority


def test_no_8833_when_no_treaty_position_is_taken(engine):
    facts = build_fact_base(lob_qualified=None)
    assert results_for(engine, facts, form="8833") == []


def test_1446_withholding_produces_reconciliation_requirement(engine):
    facts = build_fact_base(withholding_a=31_080.0)
    found = results_for(engine, facts, entity_id=HOLDCO_A, form="8805")

    assert len(found) == 1
    assert found[0].requirement is Requirement.REQUIRED
    assert "payee TIN" in found[0].rationale


def test_form_8865_is_answered_explicitly_as_not_required(engine):
    """The client asked about 8865 by name. Silence is not an answer."""
    facts = build_fact_base()
    found = results_for(engine, facts, entity_id=HOLDCO_A, form="8865")

    assert len(found) == 1
    assert found[0].requirement is Requirement.NOT_REQUIRED
    assert "mirror image" in found[0].rationale
    assert "6038" in found[0].authority


def test_usrpi_disposition_triggers_firpta_reporting(engine):
    facts = build_fact_base(usrpi_gain=410_000.0)
    found = results_for(engine, facts, entity_id=HOLDCO_A, form="8288-A")

    assert len(found) == 1
    assert "897" in found[0].authority


def test_no_firpta_reporting_without_a_disposition(engine):
    facts = build_fact_base(usrpi_gain=0.0)
    assert results_for(engine, facts, form="8288-A") == []


def test_ebie_is_tracked_per_partnership(engine):
    facts = build_fact_base()
    found = results_for(engine, facts, entity_id=HOLDCO_A, form="8990")

    assert len(found) == 1
    assert "same" in found[0].rationale  # released only by ETI from the same partnership
    assert "163(j)" in found[0].authority


def test_loss_limitation_runs_in_statutory_order(engine):
    facts = build_fact_base(holdco_b_rental=-32_000.0)
    found = results_for(engine, facts, entity_id=HOLDCO_B, rule_id="R-BASIS-LIMIT")

    assert len(found) == 1
    rationale = found[0].rationale
    assert rationale.index("704(d)") < rationale.index("465")
    assert rationale.index("465") < rationale.index("469")
    assert "465(b)(6)" in found[0].authority


def test_qualified_nonrecourse_debt_is_at_risk(engine):
    """§465(b)(6) is the real-estate exception; without it the at-risk step would bite."""
    facts = build_fact_base(holdco_b_rental=-32_000.0)
    found = results_for(engine, facts, entity_id=HOLDCO_B, rule_id="R-BASIS-LIMIT")[0]

    assert found.triggering_facts["at_risk"] > found.triggering_facts["outside_basis"]
    assert found.triggering_facts["limited_by_at_risk"] is False


def test_extension_is_recommended_by_default(engine):
    """K-1s arrive late. Extending is free; filing late is not."""
    facts = build_fact_base()
    found = results_for(engine, facts, form="7004")

    assert len(found) == 2  # one per holdco
    assert all(r.requirement is Requirement.RECOMMENDED for r in found)


def test_us_partnerships_do_not_get_foreign_corporation_rules(engine):
    facts = build_fact_base()
    lp_results = [r for r in engine.run(facts) if r.entity_id.startswith("lp-")]

    assert not [r for r in lp_results if r.form == "1120-F"]


def test_rule_set_is_versioned_by_year(engine):
    with pytest.raises(ValueError, match="No rule set registered"):
        DeterminationEngine(1999)


def test_engine_output_is_deterministic(engine):
    """Same facts, same answer — twice, in the same order."""
    facts = build_fact_base()
    first = [(r.rule_id, r.entity_id, r.form, r.requirement) for r in engine.run(facts)]
    second = [(r.rule_id, r.entity_id, r.form, r.requirement) for r in engine.run(facts)]

    assert first == second
