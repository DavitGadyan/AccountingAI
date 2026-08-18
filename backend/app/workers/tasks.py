"""Background jobs.

Extraction is slow and bursty — five syndications all sending K-1s in the same week —
so it runs off the request path. The API records intent; the worker does the work.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models import Document, ExtractedField, ExtractionJob, K1Record
from app.models.enums import DocumentKind, DocumentStatus
from app.services.extraction import (
    PROMPT_VERSION,
    ExtractionClient,
    StubExtractionClient,
    extract_pdf_text,
)
from app.services.storage import InMemoryStore, ObjectStore

log = get_logger(__name__)


def _client() -> ExtractionClient:
    if settings.anthropic_api_key:
        return ExtractionClient()
    # No key configured: the pipeline still runs end to end against the stub, which is
    # what makes local development and CI possible without spend.
    return StubExtractionClient()


def _store() -> ObjectStore:
    return ObjectStore() if settings.s3_endpoint else InMemoryStore()


async def process_document(ctx: dict, document_id: str) -> dict:
    """Classify, extract, and land a reviewed-pending K-1 record."""
    async with SessionLocal() as session:
        document = await session.get(Document, document_id)
        if document is None:
            return {"status": "missing"}

        document.status = DocumentStatus.CLASSIFYING
        await session.commit()

        raw = _store().get(document.storage_key)
        text = extract_pdf_text(raw)
        client = _client()

        kind, confidence, tax_year = await client.classify(text)
        document.kind = kind
        document.kind_confidence = confidence
        document.tax_year = tax_year or document.tax_year

        if kind not in {DocumentKind.K1_1065, DocumentKind.K3_1065}:
            # Anything that is not a K-1/K-3 is filed for the record and left for a human.
            document.status = DocumentStatus.NEEDS_REVIEW
            await session.commit()
            return {"status": "classified_only", "kind": kind.value}

        document.status = DocumentStatus.EXTRACTING
        job = ExtractionJob(
            firm_id=document.firm_id,
            document_id=document.id,
            model=client.model,
            prompt_version=PROMPT_VERSION,
            status="running",
            started_at=datetime.now(UTC),
        )
        session.add(job)
        await session.flush()

        result = await client.extract_k1(text)

        for value in result.values:
            session.add(
                ExtractedField(
                    firm_id=document.firm_id,
                    job_id=job.id,
                    document_id=document.id,
                    field_path=value.path,
                    label=value.label,
                    raw_value=value.raw_value,
                    numeric_value=value.numeric_value,
                    confidence=value.confidence,
                    page=value.page,
                    source_text=value.source_text,
                    status=value.status,
                )
            )

        job.status = "completed"
        job.finished_at = datetime.now(UTC)
        job.input_tokens = result.input_tokens
        job.output_tokens = result.output_tokens

        payload = result.as_boxes()
        if document.source_entity_id and document.recipient_entity_id:
            session.add(
                K1Record(
                    firm_id=document.firm_id,
                    engagement_id=document.engagement_id,
                    document_id=document.id,
                    partnership_entity_id=document.source_entity_id,
                    partner_entity_id=document.recipient_entity_id,
                    tax_year=document.tax_year or 0,
                    form_year=document.tax_year or 0,
                    boxes=payload.get("boxes", {}),
                    capital_account=payload.get("capital_account", {}),
                    liabilities=payload.get("liabilities", {}),
                    k3=payload.get("k3", {}),
                    withholding_1446=payload.get("boxes", {}).get("box_15_O"),
                )
            )

        # Any field the model was unsure about holds the document in review. The rules
        # engine reads reviewed data only.
        document.status = (
            DocumentStatus.NEEDS_REVIEW
            if result.needs_review_count
            else DocumentStatus.ACCEPTED
        )
        await session.commit()

        log.info(
            "document.extracted",
            document_id=document_id,
            fields=len(result.values),
            needs_review=result.needs_review_count,
            auto_accept_rate=round(result.auto_accept_rate, 3),
        )
        return {
            "status": "extracted",
            "fields": len(result.values),
            "needs_review": result.needs_review_count,
        }


async def supersede_amended(ctx: dict, document_id: str) -> dict:
    """An amended K-1 replaces the original rather than sitting beside it.

    Two live K-1s for the same partnership is how a number gets counted twice.
    """
    async with SessionLocal() as session:
        document = await session.get(Document, document_id)
        if document is None or not document.is_amended:
            return {"status": "not_amended"}

        prior = list(
            await session.scalars(
                select(Document).where(
                    Document.engagement_id == document.engagement_id,
                    Document.source_entity_id == document.source_entity_id,
                    Document.kind == document.kind,
                    Document.id != document.id,
                )
            )
        )
        for p in prior:
            p.status = DocumentStatus.SUPERSEDED
        document.supersedes_document_id = prior[0].id if prior else None
        await session.commit()
        return {"status": "superseded", "count": len(prior)}


class WorkerSettings:
    functions = [process_document, supersede_amended]
    redis_settings = settings.redis_url
