from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, File, Form, UploadFile, status
from sqlalchemy import select

from app.api.deps import EngagementDep, FirmDep, SessionDep, StaffDep
from app.core.errors import ConflictError, NotFound
from app.models import AuditEvent, Document, ExtractedField, ExtractionJob, K1Record
from app.models.enums import DocumentStatus, ExtractionFieldStatus
from app.schemas.documents import (
    DocumentOut,
    ExtractedFieldOut,
    ExtractionSummary,
    FieldReviewRequest,
    K1RecordOut,
)
from app.services.storage import digest

router = APIRouter(prefix="/engagements/{engagement_id}/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    engagement: EngagementDep, session: SessionDep, _: StaffDep, kind: str | None = None
) -> list[Document]:
    query = select(Document).where(Document.engagement_id == engagement.id)
    if kind:
        query = query.where(Document.kind == kind)
    return list(await session.scalars(query.order_by(Document.created_at.desc())))


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    engagement: EngagementDep,
    session: SessionDep,
    firm_id: FirmDep,
    user: StaffDep,
    file: UploadFile = File(...),  # noqa: B008 — FastAPI's documented upload idiom
    source_entity_id: str | None = Form(None),
    recipient_entity_id: str | None = Form(None),
) -> Document:
    """Upload a document.

    Deduplicated on content hash. Syndicators re-send the same PDF repeatedly, and
    re-extracting an identical file is wasted money and a second set of review rows.
    """
    raw = await file.read()
    sha = digest(raw)

    duplicate = await session.scalar(
        select(Document).where(
            Document.engagement_id == engagement.id, Document.sha256 == sha
        )
    )
    if duplicate is not None:
        raise ConflictError(
            f"This exact file was already uploaded as '{duplicate.filename}'.",
            detail={"existing_document_id": duplicate.id},
        ).as_http()

    from app.services.storage import content_key

    document = Document(
        firm_id=firm_id,
        engagement_id=engagement.id,
        source_entity_id=source_entity_id,
        recipient_entity_id=recipient_entity_id,
        filename=file.filename or "upload.pdf",
        storage_key=content_key(firm_id, engagement.id, file.filename or "upload.pdf", sha),
        content_type=file.content_type or "application/pdf",
        byte_size=len(raw),
        sha256=sha,
        status=DocumentStatus.UPLOADED,
        uploaded_by_id=user.id,
    )
    session.add(document)
    await session.flush()

    session.add(
        AuditEvent(
            firm_id=firm_id,
            actor_user_id=user.id,
            engagement_id=engagement.id,
            action="document.uploaded",
            object_type="document",
            object_id=document.id,
            summary=f"Uploaded {document.filename} ({len(raw):,} bytes)",
            payload={"sha256": sha},
        )
    )
    return document


@router.get("/{document_id}/fields", response_model=list[ExtractedFieldOut])
async def list_fields(
    engagement: EngagementDep,
    document_id: str,
    session: SessionDep,
    _: StaffDep,
    needs_review_only: bool = False,
) -> list[ExtractedField]:
    query = select(ExtractedField).where(ExtractedField.document_id == document_id)
    if needs_review_only:
        query = query.where(ExtractedField.status == ExtractionFieldStatus.NEEDS_REVIEW)
    return list(await session.scalars(query.order_by(ExtractedField.field_path)))


@router.get("/{document_id}/extraction", response_model=ExtractionSummary)
async def extraction_summary(
    engagement: EngagementDep, document_id: str, session: SessionDep, _: StaffDep
) -> ExtractionSummary:
    job = await session.scalar(
        select(ExtractionJob)
        .where(ExtractionJob.document_id == document_id)
        .order_by(ExtractionJob.created_at.desc())
    )
    if job is None:
        raise NotFound("No extraction has been run for this document").as_http()

    fields = list(
        await session.scalars(
            select(ExtractedField).where(ExtractedField.job_id == job.id)
        )
    )
    counts = {s: sum(1 for f in fields if f.status == s) for s in ExtractionFieldStatus}
    total = len(fields) or 1
    return ExtractionSummary(
        document_id=document_id,
        total_fields=len(fields),
        auto_accepted=counts[ExtractionFieldStatus.AUTO_ACCEPTED],
        needs_review=counts[ExtractionFieldStatus.NEEDS_REVIEW],
        confirmed=counts[ExtractionFieldStatus.CONFIRMED],
        corrected=counts[ExtractionFieldStatus.CORRECTED],
        auto_accept_rate=1 - (counts[ExtractionFieldStatus.NEEDS_REVIEW] / total),
        model=job.model,
        prompt_version=job.prompt_version,
    )


@router.post("/fields/{field_id}/review", response_model=ExtractedFieldOut)
async def review_field(
    engagement: EngagementDep,
    field_id: str,
    payload: FieldReviewRequest,
    session: SessionDep,
    firm_id: FirmDep,
    user: StaffDep,
) -> ExtractedField:
    """Confirm or correct one extracted value.

    A correction is stored alongside the model's original rather than replacing it — the
    pair is the training signal for whether the extraction prompt is drifting, and it is
    also the evidence trail if the number is ever questioned.
    """
    field = await session.scalar(
        select(ExtractedField).where(
            ExtractedField.id == field_id, ExtractedField.firm_id == firm_id
        )
    )
    if field is None:
        raise NotFound("Field not found").as_http()

    if payload.confirmed:
        field.status = ExtractionFieldStatus.CONFIRMED
    else:
        field.status = ExtractionFieldStatus.CORRECTED
        field.corrected_value = payload.corrected_value

    field.reviewed_by_id = user.id
    field.reviewed_at = datetime.now(UTC)

    session.add(
        AuditEvent(
            firm_id=firm_id,
            actor_user_id=user.id,
            engagement_id=engagement.id,
            action="extraction.field_reviewed",
            object_type="extracted_field",
            object_id=field.id,
            summary=(
                f"Confirmed {field.label}"
                if payload.confirmed
                else f"Corrected {field.label} from {field.numeric_value} to "
                f"{payload.corrected_value}"
            ),
            payload={
                "model_value": float(field.numeric_value) if field.numeric_value else None,
                "human_value": payload.corrected_value,
                "confidence": field.confidence,
                "note": payload.note,
            },
        )
    )
    return field


@router.get("/k1-records", response_model=list[K1RecordOut])
async def list_k1_records(
    engagement: EngagementDep, session: SessionDep, _: StaffDep
) -> list[K1Record]:
    return list(
        await session.scalars(
            select(K1Record).where(K1Record.engagement_id == engagement.id)
        )
    )
