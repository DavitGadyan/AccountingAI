from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import EngagementDep, FirmDep, ReviewerDep, SessionDep, StaffDep
from app.core.errors import ConflictError, FilingBlocked, NotFound
from app.models import AuditEvent, Determination, Filing, OpenItem, Variance, Workpaper
from app.models.enums import FilingStatus, IssueStatus, Requirement
from app.schemas.filings import (
    DeterminationOut,
    DeterminationOverride,
    FilingApproval,
    FilingOut,
    GateCheck,
    OpenItemOut,
    OpenItemUpdate,
    TransmitResult,
    VarianceOut,
    WorkpaperOut,
)
from app.services.efile import FilingGate, get_transmitter

router = APIRouter(prefix="/engagements/{engagement_id}", tags=["filings"])


@router.get("/determinations", response_model=list[DeterminationOut])
async def list_determinations(
    engagement: EngagementDep,
    session: SessionDep,
    _: StaffDep,
    requirement: str | None = None,
) -> list[Determination]:
    query = select(Determination).where(Determination.engagement_id == engagement.id)
    if requirement:
        query = query.where(Determination.requirement == requirement)
    return list(
        await session.scalars(
            query.order_by(Determination.jurisdiction, Determination.form)
        )
    )


@router.post("/determinations/{determination_id}/override", response_model=DeterminationOut)
async def override_determination(
    engagement: EngagementDep,
    determination_id: str,
    payload: DeterminationOverride,
    session: SessionDep,
    firm_id: FirmDep,
    reviewer: ReviewerDep,
) -> Determination:
    """A reviewer disagrees with the engine.

    Overrides survive re-runs and appear in the client memo. An engine nobody can
    override is an engine nobody trusts, but an override nobody can see is worse.
    """
    determination = await session.scalar(
        select(Determination).where(
            Determination.id == determination_id, Determination.firm_id == firm_id
        )
    )
    if determination is None:
        raise NotFound("Determination not found").as_http()

    determination.override_requirement = Requirement(payload.requirement)
    determination.override_reason = payload.reason
    determination.overridden_by_id = reviewer.id
    determination.overridden_at = datetime.now(UTC)

    session.add(
        AuditEvent(
            firm_id=firm_id,
            actor_user_id=reviewer.id,
            engagement_id=engagement.id,
            action="determination.overridden",
            object_type="determination",
            object_id=determination.id,
            summary=(
                f"{reviewer.full_name} overrode {determination.form} from "
                f"'{determination.requirement}' to '{payload.requirement}'"
            ),
            payload={
                "rule_id": determination.rule_id,
                "engine_requirement": str(determination.requirement),
                "override_requirement": payload.requirement,
                "reason": payload.reason,
            },
        )
    )
    return determination


@router.get("/filings", response_model=list[FilingOut])
async def list_filings(
    engagement: EngagementDep, session: SessionDep, _: StaffDep
) -> list[Filing]:
    return list(
        await session.scalars(
            select(Filing).where(Filing.engagement_id == engagement.id).order_by(Filing.form)
        )
    )


@router.get("/filings/{filing_id}/gate", response_model=GateCheck)
async def gate_check(
    engagement: EngagementDep, filing_id: str, session: SessionDep, firm_id: FirmDep, _: StaffDep
) -> GateCheck:
    """What is standing between this return and the IRS. Shown in the UI before approval."""
    filing = await _get_filing(session, filing_id, firm_id)
    approver = None
    if filing.approved_by_id:
        from app.models import User

        approver = await session.get(User, filing.approved_by_id)

    open_items = list(
        await session.scalars(select(OpenItem).where(OpenItem.engagement_id == engagement.id))
    )
    blockers = FilingGate.check(filing, approver, open_items)
    return GateCheck(filing_id=filing.id, transmittable=not blockers, blockers=blockers)


@router.post("/filings/{filing_id}/approve", response_model=FilingOut)
async def approve_filing(
    engagement: EngagementDep,
    filing_id: str,
    payload: FilingApproval,
    session: SessionDep,
    firm_id: FirmDep,
    reviewer: ReviewerDep,
) -> Filing:
    """Signer approval. Requires a credential on file — checked here and again at the gate."""
    filing = await _get_filing(session, filing_id, firm_id)

    if not payload.attestation:
        raise ConflictError("Approval requires the reviewer's attestation.").as_http()
    if not reviewer.credential:
        raise ConflictError(
            f"{reviewer.full_name} has no CPA/EA credential recorded. Circular 230 requires "
            f"a credentialed signer before a return can be approved."
        ).as_http()

    filing.status = FilingStatus.APPROVED
    filing.approved_by_id = reviewer.id
    filing.approved_at = datetime.now(UTC)

    session.add(
        AuditEvent(
            firm_id=firm_id,
            actor_user_id=reviewer.id,
            engagement_id=engagement.id,
            action="filing.approved",
            object_type="filing",
            object_id=filing.id,
            summary=(
                f"{reviewer.full_name} ({reviewer.credential} "
                f"{reviewer.credential_number or ''}) approved {filing.form} for "
                f"{filing.tax_year}"
            ),
            payload={"note": payload.note, "credential": reviewer.credential},
        )
    )
    return filing


@router.post("/filings/{filing_id}/transmit", response_model=TransmitResult)
async def transmit_filing(
    engagement: EngagementDep,
    filing_id: str,
    session: SessionDep,
    firm_id: FirmDep,
    reviewer: ReviewerDep,
) -> TransmitResult:
    """Transmit an approved return.

    Every gate condition is re-checked here rather than trusted from the approve call —
    an open item can be reopened between approval and transmission.
    """
    filing = await _get_filing(session, filing_id, firm_id)

    from app.models import User

    approver = await session.get(User, filing.approved_by_id) if filing.approved_by_id else None
    open_items = list(
        await session.scalars(select(OpenItem).where(OpenItem.engagement_id == engagement.id))
    )

    try:
        FilingGate.assert_transmittable(filing, approver, open_items)
    except FilingBlocked as exc:
        raise exc.as_http() from exc

    receipt = await get_transmitter().transmit(filing, filing.form_data)

    filing.status = FilingStatus.ACCEPTED if receipt.accepted else FilingStatus.REJECTED
    filing.submission_id = receipt.submission_id
    filing.transmitted_at = receipt.received_at
    filing.acknowledged_at = receipt.received_at if receipt.accepted else None
    filing.ack_reference = receipt.reference
    filing.reject_codes = receipt.reject_codes

    session.add(
        AuditEvent(
            firm_id=firm_id,
            actor_user_id=reviewer.id,
            engagement_id=engagement.id,
            action="filing.transmitted",
            object_type="filing",
            object_id=filing.id,
            summary=(
                f"Transmitted {filing.form} — submission {receipt.submission_id} "
                f"({'accepted' if receipt.accepted else 'rejected'})"
            ),
            payload={"submission_id": receipt.submission_id, "reference": receipt.reference},
        )
    )

    return TransmitResult(
        filing_id=filing.id,
        submission_id=receipt.submission_id,
        accepted=receipt.accepted,
        reference=receipt.reference,
        transmitted_at=receipt.received_at,
    )


@router.get("/workpapers", response_model=list[WorkpaperOut])
async def list_workpapers(
    engagement: EngagementDep, session: SessionDep, _: StaffDep
) -> list[Workpaper]:
    return list(
        await session.scalars(
            select(Workpaper).where(Workpaper.engagement_id == engagement.id).order_by(
                Workpaper.code
            )
        )
    )


@router.get("/open-items", response_model=list[OpenItemOut])
async def list_open_items(
    engagement: EngagementDep, session: SessionDep, _: StaffDep
) -> list[OpenItem]:
    return list(
        await session.scalars(
            select(OpenItem)
            .where(OpenItem.engagement_id == engagement.id)
            .order_by(OpenItem.blocks_filing.desc(), OpenItem.severity)
        )
    )


@router.patch("/open-items/{item_id}", response_model=OpenItemOut)
async def update_open_item(
    engagement: EngagementDep,
    item_id: str,
    payload: OpenItemUpdate,
    session: SessionDep,
    firm_id: FirmDep,
    user: StaffDep,
) -> OpenItem:
    item = await session.scalar(
        select(OpenItem).where(OpenItem.id == item_id, OpenItem.firm_id == firm_id)
    )
    if item is None:
        raise NotFound("Open item not found").as_http()

    new_status = IssueStatus(payload.status)
    # Waiving a blocking item is a reviewer decision, not a preparer one.
    if new_status == IssueStatus.WAIVED and str(user.role) not in {"reviewer", "admin"}:
        raise ConflictError(
            "Only a reviewer may waive an open item that blocks filing."
        ).as_http()
    if new_status in {IssueStatus.RESOLVED, IssueStatus.WAIVED} and not payload.resolution_note:
        raise ConflictError(
            "Resolving or waiving an item requires a note explaining how it was resolved."
        ).as_http()

    item.status = new_status
    item.resolution_note = payload.resolution_note
    item.resolved_by_id = user.id
    item.resolved_at = datetime.now(UTC)

    session.add(
        AuditEvent(
            firm_id=firm_id,
            actor_user_id=user.id,
            engagement_id=engagement.id,
            action=f"open_item.{payload.status}",
            object_type="open_item",
            object_id=item.id,
            summary=f"{item.title} -> {payload.status}",
            payload={"note": payload.resolution_note},
        )
    )
    return item


@router.get("/variances", response_model=list[VarianceOut])
async def list_variances(
    engagement: EngagementDep, session: SessionDep, _: StaffDep
) -> list[Variance]:
    return list(
        await session.scalars(
            select(Variance)
            .where(Variance.engagement_id == engagement.id)
            .order_by(Variance.is_material.desc())
        )
    )


async def _get_filing(session, filing_id: str, firm_id: str) -> Filing:
    filing = await session.scalar(
        select(Filing).where(Filing.id == filing_id, Filing.firm_id == firm_id)
    )
    if filing is None:
        raise NotFound("Filing not found").as_http()
    return filing
