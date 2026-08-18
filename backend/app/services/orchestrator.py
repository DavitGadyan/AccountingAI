"""The engagement pipeline.

One function per stage, one function that runs them in order. The API layer calls this;
it never re-implements a stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import (
    Client,
    Determination,
    Engagement,
    Entity,
    Filing,
    OpenItem,
    Variance,
    Workpaper,
)
from app.models.enums import FilingStatus, Requirement
from app.rules.base import FactBase, RuleResult
from app.rules.engine import DeterminationEngine
from app.services import completeness, memo, tieout, workpapers
from app.services.factbase import build_fact_base

log = get_logger(__name__)


@dataclass
class PipelineReport:
    engagement_id: str
    tax_year: int
    rules_evaluated: int
    determinations: list[RuleResult] = field(default_factory=list)
    workpapers_generated: int = 0
    open_items: int = 0
    blocking_items: int = 0
    variances: int = 0
    memo_markdown: str = ""

    @property
    def required_filings(self) -> list[RuleResult]:
        return [
            d
            for d in self.determinations
            if d.requirement in {Requirement.REQUIRED, Requirement.PROTECTIVE}
        ]


async def run_determination(session: AsyncSession, engagement_id: str) -> PipelineReport:
    """Stages 3–8 of the engagement, in one idempotent pass.

    Re-running replaces the prior computed output for the engagement. Human decisions —
    reviewer overrides, resolved open items, approved filings — are preserved, because
    re-running a determination must never silently discard someone's judgement.
    """
    engagement = await session.get(Engagement, engagement_id)
    if engagement is None:
        raise ValueError(f"Engagement {engagement_id} not found")
    client = await session.get(Client, engagement.client_id)

    facts = await build_fact_base(session, engagement_id)
    engine = DeterminationEngine(engagement.tax_year)
    results = engine.run(facts)

    await _persist_determinations(session, engagement, results)

    coverage = engine.coverage()
    drafts = workpapers.generate_all(facts, results, coverage)
    await _persist_workpapers(session, engagement, drafts)

    expected = await _expected_k1_counts(session, facts)
    item_drafts = completeness.detect(facts, results, expected)
    await _persist_open_items(session, engagement, item_drafts)

    prior = await _prior_snapshot(session, engagement)
    variance_drafts = tieout.compare(facts, prior) if prior else []
    await _persist_variances(session, engagement, variance_drafts)

    await _sync_filings(session, engagement, results)

    memo_md = memo.build_memo(
        facts, results, variance_drafts, client.display_name if client else "Client"
    )

    await session.flush()

    return PipelineReport(
        engagement_id=engagement_id,
        tax_year=engagement.tax_year,
        rules_evaluated=engine.rule_count,
        determinations=results,
        workpapers_generated=len(drafts),
        open_items=len(item_drafts),
        blocking_items=sum(1 for i in item_drafts if i.blocks_filing),
        variances=len(variance_drafts),
        memo_markdown=memo_md,
    )


async def _persist_determinations(
    session: AsyncSession, engagement: Engagement, results: list[RuleResult]
) -> None:
    existing = list(
        await session.scalars(
            select(Determination).where(Determination.engagement_id == engagement.id)
        )
    )
    # A reviewer override is a human decision; a re-run must not erase it.
    overrides = {
        (d.rule_id, d.entity_id, d.form): d for d in existing if d.override_requirement is not None
    }
    for d in existing:
        if (d.rule_id, d.entity_id, d.form) not in overrides:
            await session.delete(d)

    for r in results:
        key = (r.rule_id, r.entity_id, r.form)
        if key in overrides:
            kept = overrides[key]
            kept.rationale = r.rationale
            kept.authority = r.authority
            kept.triggering_facts = r.triggering_facts
            kept.requirement = r.requirement
            continue
        session.add(
            Determination(
                firm_id=engagement.firm_id,
                engagement_id=engagement.id,
                entity_id=r.entity_id,
                tax_year=engagement.tax_year,
                rule_id=r.rule_id,
                rule_version=r.rule_version,
                form=r.form,
                jurisdiction=r.jurisdiction,
                state=r.state,
                requirement=r.requirement,
                rationale=r.rationale,
                authority=r.authority,
                triggering_facts=r.triggering_facts,
                confidence=r.confidence,
                due_date=r.due_date,
                extended_due_date=r.extended_due_date,
            )
        )


async def _persist_workpapers(
    session: AsyncSession, engagement: Engagement, drafts: list
) -> None:
    for wp in await session.scalars(
        select(Workpaper).where(Workpaper.engagement_id == engagement.id)
    ):
        await session.delete(wp)
    for d in drafts:
        session.add(
            Workpaper(
                firm_id=engagement.firm_id,
                engagement_id=engagement.id,
                entity_id=d.entity_id,
                code=d.code,
                title=d.title,
                generator_version=workpapers.GENERATOR_VERSION,
                rows=d.rows,
                totals=d.totals,
                narrative=d.narrative,
                ties_out=d.ties_out,
                tie_out_detail=d.tie_out_detail,
            )
        )


async def _persist_open_items(
    session: AsyncSession, engagement: Engagement, drafts: list
) -> None:
    existing = list(
        await session.scalars(select(OpenItem).where(OpenItem.engagement_id == engagement.id))
    )
    # Resolutions are human decisions and survive a re-run.
    resolved = {i.code for i in existing if i.status.value in {"resolved", "waived"}}
    for i in existing:
        if i.code not in resolved:
            await session.delete(i)

    for d in drafts:
        if d.code in resolved:
            continue
        session.add(
            OpenItem(
                firm_id=engagement.firm_id,
                engagement_id=engagement.id,
                entity_id=d.entity_id,
                code=d.code,
                title=d.title,
                detail=d.detail,
                severity=d.severity,
                blocks_filing=d.blocks_filing,
                requested_from=d.requested_from,
            )
        )


async def _persist_variances(session: AsyncSession, engagement: Engagement, drafts: list) -> None:
    for v in await session.scalars(
        select(Variance).where(Variance.engagement_id == engagement.id)
    ):
        await session.delete(v)
    for d in drafts:
        session.add(
            Variance(
                firm_id=engagement.firm_id,
                engagement_id=engagement.id,
                entity_id=d.entity_id,
                metric=d.metric,
                prior_year=engagement.tax_year - 1,
                prior_value=d.prior_value,
                current_value=d.current_value,
                absolute_change=d.absolute_change,
                relative_change=d.relative_change,
                is_material=d.is_material,
                explanation=d.explanation,
            )
        )


async def _sync_filings(
    session: AsyncSession, engagement: Engagement, results: list[RuleResult]
) -> None:
    """Create a Filing shell for each required return, without disturbing filed ones."""
    existing = {
        (f.form, f.entity_id, f.state): f
        for f in await session.scalars(
            select(Filing).where(Filing.engagement_id == engagement.id)
        )
    }
    for r in results:
        if r.requirement not in {Requirement.REQUIRED, Requirement.PROTECTIVE}:
            continue
        if r.form.startswith("Loss limitation") or "workpaper" in r.form.lower():
            continue
        key = (r.form, r.entity_id, r.state)
        if key in existing:
            continue
        session.add(
            Filing(
                firm_id=engagement.firm_id,
                engagement_id=engagement.id,
                entity_id=r.entity_id,
                form=r.form,
                tax_year=engagement.tax_year,
                jurisdiction=r.jurisdiction,
                state=r.state,
                is_protective=r.requirement == Requirement.PROTECTIVE,
                is_extension=r.form == "7004",
                status=FilingStatus.NOT_STARTED,
            )
        )


async def _expected_k1_counts(session: AsyncSession, facts: FactBase) -> dict[str, int]:
    """How many K-1s *should* arrive: one per U.S. partnership held."""
    counts: dict[str, int] = {}
    for e in facts.entities:
        held = [
            owned
            for owner, owned, _ in facts.ownership_edges
            if owner == e.entity_id
        ]
        if not held:
            continue
        n = 0
        for h in held:
            entity = await session.get(Entity, h)
            if entity and entity.country == "US" and str(entity.entity_type) in {
                "us_partnership",
                "us_llc",
            }:
                n += 1
        if n:
            counts[e.entity_id] = n
    return counts


async def _prior_snapshot(
    session: AsyncSession, engagement: Engagement
) -> dict[str, dict[str, float]] | None:
    prior = await session.scalar(
        select(Engagement).where(
            Engagement.client_id == engagement.client_id,
            Engagement.tax_year == engagement.tax_year - 1,
        )
    )
    if prior is None:
        return None
    prior_facts = await build_fact_base(session, prior.id)
    return tieout.snapshot(prior_facts)
