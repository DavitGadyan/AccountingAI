from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import func, select

from app.api.deps import EngagementDep, FirmDep, SessionDep, StaffDep
from app.core.errors import ConflictError, NotFound
from app.models import (
    AuditEvent,
    Client,
    Determination,
    Document,
    Engagement,
    Entity,
    ExtractedField,
    Filing,
    OpenItem,
    Ownership,
)
from app.models.enums import ExtractionFieldStatus, FilingStatus, IssueStatus, Requirement
from app.schemas.entities import EngagementCreate, EngagementDashboard, EngagementOut
from app.schemas.filings import MemoOut, PipelineReportOut
from app.services.orchestrator import run_determination

router = APIRouter(prefix="/engagements", tags=["engagements"])


@router.get("", response_model=list[EngagementOut])
async def list_engagements(
    session: SessionDep, firm_id: FirmDep, _: StaffDep, tax_year: int | None = None
) -> list[Engagement]:
    query = select(Engagement).where(Engagement.firm_id == firm_id)
    if tax_year is not None:
        query = query.where(Engagement.tax_year == tax_year)
    return list(await session.scalars(query.order_by(Engagement.tax_year.desc())))


@router.post("", response_model=EngagementOut, status_code=status.HTTP_201_CREATED)
async def create_engagement(
    payload: EngagementCreate, session: SessionDep, firm_id: FirmDep, user: StaffDep
) -> Engagement:
    existing = await session.scalar(
        select(Engagement).where(
            Engagement.client_id == payload.client_id, Engagement.tax_year == payload.tax_year
        )
    )
    if existing:
        raise ConflictError(
            f"An engagement for tax year {payload.tax_year} already exists for this client."
        ).as_http()

    prior = await session.scalar(
        select(Engagement).where(
            Engagement.client_id == payload.client_id,
            Engagement.tax_year == payload.tax_year - 1,
        )
    )
    engagement = Engagement(
        firm_id=firm_id,
        **payload.model_dump(),
        is_first_year=prior is None,
        rolled_from_engagement_id=prior.id if prior else None,
    )
    session.add(engagement)
    await session.flush()

    session.add(
        AuditEvent(
            firm_id=firm_id,
            actor_user_id=user.id,
            engagement_id=engagement.id,
            action="engagement.created",
            object_type="engagement",
            object_id=engagement.id,
            summary=(
                f"Created {payload.tax_year} engagement"
                + (f", rolled from {prior.tax_year}" if prior else " (first year)")
            ),
            payload={"rolled_from": prior.id if prior else None},
        )
    )
    return engagement


@router.get("/{engagement_id}", response_model=EngagementDashboard)
async def dashboard(
    engagement: EngagementDep, session: SessionDep, firm_id: FirmDep, _: StaffDep
) -> EngagementDashboard:
    client = await session.get(Client, engagement.client_id)

    docs = await session.scalar(
        select(func.count()).select_from(Document).where(Document.engagement_id == engagement.id)
    )
    needs_review = await session.scalar(
        select(func.count())
        .select_from(ExtractedField)
        .join(Document, Document.id == ExtractedField.document_id)
        .where(
            Document.engagement_id == engagement.id,
            ExtractedField.status == ExtractionFieldStatus.NEEDS_REVIEW,
        )
    )
    determinations = await session.scalar(
        select(func.count())
        .select_from(Determination)
        .where(Determination.engagement_id == engagement.id)
    )
    filings = list(
        await session.scalars(select(Filing).where(Filing.engagement_id == engagement.id))
    )
    open_items = list(
        await session.scalars(select(OpenItem).where(OpenItem.engagement_id == engagement.id))
    )

    # Expected documents: one K-1 per U.S. partnership held by any client entity.
    entity_ids = {
        e.id
        for e in await session.scalars(
            select(Entity).where(Entity.client_id == engagement.client_id)
        )
    }
    held = list(
        await session.scalars(
            select(Ownership).where(Ownership.owner_entity_id.in_(entity_ids))
        )
    )
    expected = 0
    for edge in held:
        target = await session.get(Entity, edge.owned_entity_id)
        if target and target.country == "US" and str(target.entity_type) in {
            "us_partnership",
            "us_llc",
        }:
            expected += 2  # a K-1 and a K-3 are both expected from each partnership

    upcoming = [
        d.extended_due_date or d.due_date
        for d in await session.scalars(
            select(Determination).where(
                Determination.engagement_id == engagement.id,
                Determination.requirement.in_(
                    [Requirement.REQUIRED, Requirement.PROTECTIVE]
                ),
            )
        )
        if (d.extended_due_date or d.due_date)
    ]

    return EngagementDashboard(
        engagement=EngagementOut.model_validate(engagement),
        client_name=client.display_name if client else "",
        documents_received=int(docs or 0),
        documents_expected=expected,
        fields_needing_review=int(needs_review or 0),
        determinations=int(determinations or 0),
        filings_required=len(filings),
        filings_accepted=sum(1 for f in filings if f.status == FilingStatus.ACCEPTED),
        open_items_blocking=sum(
            1
            for i in open_items
            if i.blocks_filing and i.status not in {IssueStatus.RESOLVED, IssueStatus.WAIVED}
        ),
        open_items_total=len(open_items),
        next_due_date=min(upcoming) if upcoming else None,
        memo_available=determinations > 0,
    )


@router.post("/{engagement_id}/determine", response_model=PipelineReportOut)
async def determine(
    engagement: EngagementDep, session: SessionDep, firm_id: FirmDep, user: StaffDep
) -> PipelineReportOut:
    """Run the determination pipeline.

    Idempotent: re-running replaces computed output but preserves every human decision —
    reviewer overrides, resolved open items and approved filings all survive.
    """
    report = await run_determination(session, engagement.id)

    session.add(
        AuditEvent(
            firm_id=firm_id,
            actor_user_id=user.id,
            engagement_id=engagement.id,
            action="determination.run",
            object_type="engagement",
            object_id=engagement.id,
            summary=(
                f"Evaluated {report.rules_evaluated} rules; produced "
                f"{len(report.determinations)} determinations and "
                f"{report.blocking_items} blocking open items"
            ),
            payload={
                "rules_evaluated": report.rules_evaluated,
                "determinations": len(report.determinations),
            },
        )
    )

    return PipelineReportOut(
        engagement_id=report.engagement_id,
        tax_year=report.tax_year,
        rules_evaluated=report.rules_evaluated,
        determinations=len(report.determinations),
        filings_required=len(report.required_filings),
        workpapers_generated=report.workpapers_generated,
        open_items=report.open_items,
        blocking_items=report.blocking_items,
        variances=report.variances,
    )


@router.get("/{engagement_id}/memo", response_model=MemoOut)
async def memo(engagement: EngagementDep, session: SessionDep, _: StaffDep) -> MemoOut:
    report = await run_determination(session, engagement.id)
    if not report.memo_markdown:
        raise NotFound("No memo available — run the determination first").as_http()
    return MemoOut(engagement_id=engagement.id, markdown=report.memo_markdown)


@router.post("/{engagement_id}/rollforward", response_model=EngagementOut)
async def rollforward(
    engagement: EngagementDep, session: SessionDep, firm_id: FirmDep, user: StaffDep
) -> Engagement:
    """Create next year's engagement from this one.

    Year two of an unchanged structure should be a re-run, not a rebuild — the entity
    graph, property states and elections all carry over untouched.
    """
    next_year = engagement.tax_year + 1
    existing = await session.scalar(
        select(Engagement).where(
            Engagement.client_id == engagement.client_id, Engagement.tax_year == next_year
        )
    )
    if existing:
        raise ConflictError(f"A {next_year} engagement already exists.").as_http()

    new = Engagement(
        firm_id=firm_id,
        client_id=engagement.client_id,
        tax_year=next_year,
        fixed_fee=engagement.fixed_fee,
        fee_currency=engagement.fee_currency,
        is_first_year=False,
        assigned_preparer_id=engagement.assigned_preparer_id,
        assigned_reviewer_id=engagement.assigned_reviewer_id,
        rolled_from_engagement_id=engagement.id,
    )
    session.add(new)
    await session.flush()

    session.add(
        AuditEvent(
            firm_id=firm_id,
            actor_user_id=user.id,
            engagement_id=new.id,
            action="engagement.rolled_forward",
            object_type="engagement",
            object_id=new.id,
            summary=f"Rolled {engagement.tax_year} engagement forward to {next_year}",
            payload={"source_engagement_id": engagement.id},
        )
    )
    return new
