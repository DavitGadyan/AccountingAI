"""Rule execution.

Import order matters only in that every rule module must be imported before ``run`` is
called, so that the decorators have populated the registry.
"""

from __future__ import annotations

from app.rules import crossborder, federal, state  # noqa: F401  (registration side effects)
from app.rules.base import FactBase, RuleResult, registry


class DeterminationEngine:
    """Runs every registered rule for a tax year against a fact base.

    Rules are independent: no rule may read another rule's output. If two rules disagree
    the disagreement is surfaced to the reviewer rather than resolved by ordering, because
    ordering-dependent tax logic is impossible to audit.
    """

    def __init__(self, tax_year: int) -> None:
        self.tax_year = tax_year
        self._rules = registry.for_year(tax_year)
        if not self._rules:
            raise ValueError(
                f"No rule set registered for tax year {tax_year}. "
                "Rules are versioned by year deliberately — add a rule set before running."
            )

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def run(self, facts: FactBase) -> list[RuleResult]:
        results: list[RuleResult] = []
        for _rule_id, _title, fn in self._rules:
            results.extend(fn(facts))
        return sorted(results, key=lambda r: (r.jurisdiction, r.state or "", r.form, r.rule_id))

    def coverage(self) -> dict[str, str]:
        """Which rules were evaluated. Shown to the reviewer as an assurance list."""
        return registry.titles(self.tax_year)
