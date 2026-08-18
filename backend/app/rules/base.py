"""Rule primitives.

Determination is deterministic Python, never a model call. The same facts must produce
the same forms in five years' time, and every output must carry the authority it rests on.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from app.models.enums import Requirement


@dataclass(frozen=True)
class EntityFacts:
    """Everything a rule may look at for one entity. Flat and immutable on purpose."""

    entity_id: str
    name: str
    entity_type: str
    tax_classification: str
    country: str
    formation_state: str | None = None
    us_tin: str | None = None
    treaty_country: str | None = None
    treaty_lob_qualified: bool | None = None
    net_election_871d: bool = False
    is_syndication: bool = False
    exited: bool = False

    # Aggregated from the K-1s allocated to this entity
    eci_income: float = 0.0
    fdap_income: float = 0.0
    rental_income: float = 0.0
    ordinary_income: float = 0.0
    section_1231_gain: float = 0.0
    capital_gain: float = 0.0
    usrpi_gain: float = 0.0            # §897 gain
    withholding_1446: float = 0.0
    withholding_1445: float = 0.0
    withholding_1042: float = 0.0
    excess_business_interest: float = 0.0
    allocated_loss: float = 0.0
    outside_basis: float = 0.0
    at_risk_amount: float = 0.0
    qualified_nonrecourse_debt: float = 0.0

    holds_us_partnership_interest: bool = False
    disposed_partnership_interest: bool = False
    partnership_disposed_usrpi: bool = False
    has_reportable_related_party_transactions: bool = False
    us_owner_above: bool = False        # a U.S. person sits above this entity
    property_states: tuple[str, ...] = ()
    composite_states: tuple[str, ...] = ()
    state_amounts: dict[str, float] = field(default_factory=dict)

    prior_year_forms: tuple[str, ...] = ()
    k1_count: int = 0
    k3_count: int = 0


@dataclass(frozen=True)
class FactBase:
    tax_year: int
    engagement_id: str
    entities: tuple[EntityFacts, ...]
    ownership_edges: tuple[tuple[str, str, float], ...] = ()   # (owner, owned, profits_pct)
    ultimate_owner_country: str = "CA"

    def by_id(self, entity_id: str) -> EntityFacts | None:
        return next((e for e in self.entities if e.entity_id == entity_id), None)

    def owners_of(self, entity_id: str) -> list[EntityFacts]:
        ids = {owner for owner, owned, _ in self.ownership_edges if owned == entity_id}
        return [e for e in self.entities if e.entity_id in ids]

    def owned_by(self, entity_id: str) -> list[EntityFacts]:
        ids = {owned for owner, owned, _ in self.ownership_edges if owner == entity_id}
        return [e for e in self.entities if e.entity_id in ids]


@dataclass
class RuleResult:
    """What a rule emits. ``NOT_REQUIRED`` results are kept, not discarded."""

    rule_id: str
    form: str
    entity_id: str
    requirement: Requirement
    rationale: str
    authority: str
    jurisdiction: str = "us_federal"
    state: str | None = None
    triggering_facts: dict = field(default_factory=dict)
    confidence: float = 1.0
    due_date: date | None = None
    extended_due_date: date | None = None
    rule_version: str = "2025.1"


class Rule(Protocol):
    rule_id: str
    title: str

    def __call__(self, facts: FactBase) -> Iterable[RuleResult]: ...


RuleFn = Callable[[FactBase], Iterable[RuleResult]]


class RuleRegistry:
    """Rules registered per tax year.

    Versioning by year is what lets a 2031 re-run of tax year 2025 reproduce the 2025
    answer instead of silently applying five years of law changes to old facts.
    """

    def __init__(self) -> None:
        self._rules: dict[int, list[tuple[str, str, RuleFn]]] = {}

    def register(self, *, years: Iterable[int], rule_id: str, title: str):
        def decorator(fn: RuleFn) -> RuleFn:
            for year in years:
                self._rules.setdefault(year, []).append((rule_id, title, fn))
            return fn

        return decorator

    def for_year(self, year: int) -> list[tuple[str, str, RuleFn]]:
        return list(self._rules.get(year, []))

    def rule_ids(self, year: int) -> list[str]:
        return [rid for rid, _, _ in self.for_year(year)]

    def titles(self, year: int) -> dict[str, str]:
        return {rid: title for rid, title, _ in self.for_year(year)}


registry = RuleRegistry()

SUPPORTED_YEARS = (2024, 2025, 2026)
