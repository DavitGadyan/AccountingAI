"""Documents, extraction jobs and the structured K-1/K-3 record they produce."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, FirmScopedMixin, TimestampMixin, UUIDMixin
from app.models.enums import DocumentKind, DocumentStatus, ExtractionFieldStatus


class Document(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    __tablename__ = "documents"

    engagement_id: Mapped[str] = mapped_column(ForeignKey("engagements.id"), index=True)
    # Which entity in the structure this document belongs to (the partnership that issued
    # the K-1, or the holdco a prior-year return was filed for).
    source_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id"))
    recipient_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id"))

    filename: Mapped[str] = mapped_column(String(400))
    storage_key: Mapped[str] = mapped_column(String(600))
    content_type: Mapped[str] = mapped_column(String(120))
    byte_size: Mapped[int] = mapped_column()
    # Content hash. Syndicators re-send the same PDF constantly; this is what stops the
    # same K-1 being extracted and billed twice.
    sha256: Mapped[str] = mapped_column(String(64), index=True)

    kind: Mapped[DocumentKind] = mapped_column(String(40), default=DocumentKind.UNCLASSIFIED)
    kind_confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[DocumentStatus] = mapped_column(String(30), default=DocumentStatus.UPLOADED)
    tax_year: Mapped[int | None] = mapped_column(index=True)

    is_amended: Mapped[bool] = mapped_column(Boolean, default=False)
    supersedes_document_id: Mapped[str | None] = mapped_column(String(36))
    page_count: Mapped[int | None] = mapped_column()
    uploaded_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))

    extractions: Mapped[list[ExtractionJob]] = relationship(back_populates="document")


class ExtractionJob(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    __tablename__ = "extraction_jobs"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    model: Mapped[str] = mapped_column(String(80))
    prompt_version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="queued")

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_tokens: Mapped[int | None] = mapped_column()
    output_tokens: Mapped[int | None] = mapped_column()
    error: Mapped[str | None] = mapped_column(Text)

    document: Mapped[Document] = relationship(back_populates="extractions")
    fields: Mapped[list[ExtractedField]] = relationship(back_populates="job")


class ExtractedField(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """One extracted value, with the provenance a reviewer needs to check it fast.

    ``page`` and ``source_text`` exist so review is a two-second glance at the right
    part of the PDF rather than a hunt through forty pages.
    """

    __tablename__ = "extracted_fields"

    job_id: Mapped[str] = mapped_column(ForeignKey("extraction_jobs.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)

    field_path: Mapped[str] = mapped_column(String(120))  # e.g. "part_iii.box_2"
    label: Mapped[str] = mapped_column(String(200))
    raw_value: Mapped[str | None] = mapped_column(String(400))
    numeric_value: Mapped[float | None] = mapped_column(Numeric(16, 2))
    confidence: Mapped[float] = mapped_column(Float)
    page: Mapped[int | None] = mapped_column()
    source_text: Mapped[str | None] = mapped_column(Text)

    status: Mapped[ExtractionFieldStatus] = mapped_column(
        String(30), default=ExtractionFieldStatus.NEEDS_REVIEW
    )
    reviewed_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    corrected_value: Mapped[float | None] = mapped_column(Numeric(16, 2))

    job: Mapped[ExtractionJob] = relationship(back_populates="fields")

    @property
    def effective_value(self) -> float | None:
        """What the rules engine reads. A human correction always wins."""
        if self.status == ExtractionFieldStatus.CORRECTED and self.corrected_value is not None:
            return float(self.corrected_value)
        return float(self.numeric_value) if self.numeric_value is not None else None


class K1Record(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """The reviewed, structured K-1 — the fact base the rules engine actually reads.

    Line items live in ``boxes``/``k3`` JSON rather than 90 nullable columns because the
    form changes shape between years and a JSON payload versioned by ``form_year`` beats
    a migration per box.
    """

    __tablename__ = "k1_records"

    engagement_id: Mapped[str] = mapped_column(ForeignKey("engagements.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    partnership_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    partner_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)

    tax_year: Mapped[int] = mapped_column(index=True)
    form_year: Mapped[int] = mapped_column()
    is_final_k1: Mapped[bool] = mapped_column(Boolean, default=False)
    is_amended: Mapped[bool] = mapped_column(Boolean, default=False)

    partnership_ein: Mapped[str | None] = mapped_column(String(20))
    partner_is_foreign: Mapped[bool] = mapped_column(Boolean, default=True)

    # Part III boxes 1-20, keyed "box_1", "box_2", "box_13_K", "box_20_AH", ...
    boxes: Mapped[dict] = mapped_column(JSON, default=dict)
    # Capital account rollforward (tax basis method, Item L)
    capital_account: Mapped[dict] = mapped_column(JSON, default=dict)
    # Liabilities (Item K) — qualified nonrecourse drives the §465 at-risk step
    liabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    # Schedule K-3 Parts II/III/IV — the source/character detail 1120-F needs
    k3: Mapped[dict] = mapped_column(JSON, default=dict)
    # Per-state amounts from the state supplement
    state_amounts: Mapped[dict] = mapped_column(JSON, default=dict)

    withholding_1446: Mapped[float | None] = mapped_column(Numeric(14, 2))
    reviewed_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def box(self, key: str, default: float = 0.0) -> float:
        value = self.boxes.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
