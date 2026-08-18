"""Year-over-year consistency — engagement scope item 7.

The point is not to make numbers match. It is to make every number that *moved* have a
sentence next to it before a reviewer signs.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.rules.base import FactBase


@dataclass
class VarianceDraft:
    entity_id: str
    metric: str
    prior_value: float | None
    current_value: float | None
    absolute_change: float
    relative_change: float | None
    is_material: bool
    explanation: str


COMPARED_METRICS = [
    ("rental_income", "Net rental real estate income"),
    ("ordinary_income", "Ordinary business income"),
    ("withholding_1446", "§1446 withholding credit"),
    ("excess_business_interest", "Excess business interest (§163(j))"),
    ("outside_basis", "Ending capital / basis"),
    ("k1_count", "Number of K-1s received"),
]


def _explain(metric: str, prior: float, current: float, relative: float | None) -> str:
    direction = "increased" if current > prior else "decreased"
    if metric == "k1_count":
        if current < prior:
            return (
                f"K-1 count {direction} from {prior:.0f} to {current:.0f}. Either an "
                f"investment was exited — in which case a final K-1 and a §731/§751 "
                f"analysis are expected — or a K-1 has not arrived. Both need answering "
                f"before filing, and they lead to opposite conclusions."
            )
        return (
            f"K-1 count {direction} from {prior:.0f} to {current:.0f}. A new investment "
            f"was made; confirm the acquisition date, initial capital and whether the "
            f"partnership adds a new state."
        )
    if metric == "withholding_1446":
        return (
            f"§1446 withholding {direction} by {abs(relative or 0):.0%}. Withholding tracks "
            f"allocated ECTI, so a change here that does not track the income change usually "
            f"means the partnership changed its withholding assumption or issued the 8805 to "
            f"a different tier."
        )
    return (
        f"{metric} {direction} from ${prior:,.0f} to ${current:,.0f} "
        f"({abs(relative or 0):.0%}). Confirm against the partnership's own year-over-year "
        f"presentation before treating it as expected."
    )


def compare(current: FactBase, prior_snapshot: dict[str, dict[str, float]]) -> list[VarianceDraft]:
    """``prior_snapshot`` maps entity_id -> metric -> value, from the prior engagement."""
    out: list[VarianceDraft] = []
    for e in current.entities:
        prior = prior_snapshot.get(e.entity_id)
        if prior is None:
            continue
        for metric, _label in COMPARED_METRICS:
            prior_value = float(prior.get(metric, 0.0))
            current_value = float(getattr(e, metric, 0.0))
            absolute = current_value - prior_value
            relative = (absolute / abs(prior_value)) if prior_value else None

            material = abs(absolute) >= settings.variance_absolute_threshold or (
                relative is not None and abs(relative) >= settings.variance_relative_threshold
            )
            if metric == "k1_count":
                material = absolute != 0

            if not material:
                continue

            out.append(
                VarianceDraft(
                    entity_id=e.entity_id,
                    metric=metric,
                    prior_value=prior_value,
                    current_value=current_value,
                    absolute_change=absolute,
                    relative_change=relative,
                    is_material=True,
                    explanation=_explain(metric, prior_value, current_value, relative),
                )
            )
    return out


def snapshot(facts: FactBase) -> dict[str, dict[str, float]]:
    """Persisted at filing so next year has something to compare against."""
    return {
        e.entity_id: {metric: float(getattr(e, metric, 0.0)) for metric, _ in COMPARED_METRICS}
        for e in facts.entities
    }
