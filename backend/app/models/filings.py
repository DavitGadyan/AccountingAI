"""Determinations, filings, workpapers, open items, deliverables and the audit log."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, FirmScopedMixin, TimestampMixin, UUIDMixin
from app.models.enums import FilingStatus, IssueSeverity, IssueStatus, Requirement


class Determination(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """One rule firing against one entity for one year.

    A determination of ``NOT_REQUIRED`` is stored, not omitted. "We considered Form 8865
    and it does not apply because..." is a deliverable; silence is not.
    """

    __tablename__ = "determinations"

    engagement_id: Mapped[str] = mapped_column(ForeignKey("engagements.id"), index=True)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    tax_year: Mapped[int] = mapped_column(index=True)

    rule_id: Mapped[str] = mapped_column(String(60), index=True)
    rule_version: Mapped[str] = mapped_column(String(20))
    form: Mapped[str] = mapped_column(String(40))              # "1120-F", "8805", "TX-05-158"
    jurisdiction: Mapped[str] = mapped_column(String(30))
    state: Mapped[str | None] = mapped_column(String(2))

    requirement: Mapped[Requirement] = mapped_column(String(30))
    rationale: Mapped[str] = mapped_column(Text)
    authority: Mapped[str] = mapped_column(Text)               # IRC §, Reg., treaty article
    triggering_facts: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    due_date: Mapped[date | None] = mapped_column(Date)
    extended_due_date: Mapped[date | None] = mapped_column(Date)

    # A reviewer may disagree with the engine. Overrides are recorded with a reason and
    # surfaced in the memo — an engine nobody can override is an engine nobody trusts.
    overridden_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    overridden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    override_requirement: Mapped[Requirement | None] = mapped_column(String(30))
    override_reason: Mapped[str | None] = mapped_column(Text)

    @property
    def effective_requirement(self) -> Requirement:
        return self.override_requirement or self.requirement


class Filing(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """A return being prepared, reviewed, transmitted and acknowledged."""

    __tablename__ = "filings"

    engagement_id: Mapped[str] = mapped_column(ForeignKey("engagements.id"), index=True)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    determination_id: Mapped[str | None] = mapped_column(ForeignKey("determinations.id"))

    form: Mapped[str] = mapped_column(String(40))
    tax_year: Mapped[int] = mapped_column(index=True)
    jurisdiction: Mapped[str] = mapped_column(String(30))
    state: Mapped[str | None] = mapped_column(String(2))
    is_protective: Mapped[bool] = mapped_column(Boolean, default=False)
    is_extension: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[FilingStatus] = mapped_column(String(30), default=FilingStatus.NOT_STARTED)
    form_data: Mapped[dict] = mapped_column(JSON, default=dict)

    prepared_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    prepared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    submission_id: Mapped[str | None] = mapped_column(String(80), index=True)
    transmitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ack_reference: Mapped[str | None] = mapped_column(String(120))
    reject_codes: Mapped[list | None] = mapped_column(JSON)

    balance_due: Mapped[float | None] = mapped_column(Numeric(14, 2))
    overpayment: Mapped[float | None] = mapped_column(Numeric(14, 2))


class Workpaper(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """A generated supporting schedule. Reproducible from the fact base at any time."""

    __tablename__ = "workpapers"

    engagement_id: Mapped[str] = mapped_column(ForeignKey("engagements.id"), index=True)
    entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id"))
    filing_id: Mapped[str | None] = mapped_column(ForeignKey("filings.id"))

    code: Mapped[str] = mapped_column(String(40), index=True)   # "WP-BASIS", "WP-1446"
    title: Mapped[str] = mapped_column(String(250))
    generator_version: Mapped[str] = mapped_column(String(20))
    rows: Mapped[list] = mapped_column(JSON, default=list)
    totals: Mapped[dict] = mapped_column(JSON, default=dict)
    narrative: Mapped[str | None] = mapped_column(Text)
    ties_out: Mapped[bool] = mapped_column(Boolean, default=True)
    tie_out_detail: Mapped[dict] = mapped_column(JSON, default=dict)


class OpenItem(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """Missing information found before filing — engagement scope item 8."""

    __tablename__ = "open_items"

    engagement_id: Mapped[str] = mapped_column(ForeignKey("engagements.id"), index=True)
    entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id"))

    code: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str] = mapped_column(Text)
    severity: Mapped[IssueSeverity] = mapped_column(String(20), default=IssueSeverity.WARNING)
    status: Mapped[IssueStatus] = mapped_column(String(30), default=IssueStatus.OPEN)
    blocks_filing: Mapped[bool] = mapped_column(Boolean, default=False)

    requested_from: Mapped[str | None] = mapped_column(String(40))  # client | syndicator
    resolved_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)


class Variance(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """Year-over-year tie-out result — engagement scope item 7."""

    __tablename__ = "variances"

    engagement_id: Mapped[str] = mapped_column(ForeignKey("engagements.id"), index=True)
    entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id"))

    metric: Mapped[str] = mapped_column(String(120))
    prior_year: Mapped[int] = mapped_column()
    prior_value: Mapped[float | None] = mapped_column(Numeric(16, 2))
    current_value: Mapped[float | None] = mapped_column(Numeric(16, 2))
    absolute_change: Mapped[float | None] = mapped_column(Numeric(16, 2))
    relative_change: Mapped[float | None] = mapped_column(Float)
    is_material: Mapped[bool] = mapped_column(Boolean, default=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    accepted_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))


class Deliverable(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """The client package — engagement scope item 9."""

    __tablename__ = "deliverables"

    engagement_id: Mapped[str] = mapped_column(ForeignKey("engagements.id"), index=True)
    storage_key: Mapped[str] = mapped_column(String(600))
    manifest: Mapped[dict] = mapped_column(JSON, default=dict)
    memo_markdown: Mapped[str | None] = mapped_column(Text)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    released_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))


class AuditEvent(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """Append-only. Nothing in this table is ever updated or deleted.

    Circular 230 and any subsequent examination both ask the same question: who decided
    this, when, and on what facts. This table is the answer.
    """

    __tablename__ = "audit_events"

    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    engagement_id: Mapped[str | None] = mapped_column(ForeignKey("engagements.id"), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    object_type: Mapped[str] = mapped_column(String(60))
    object_id: Mapped[str | None] = mapped_column(String(36), index=True)
    summary: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(64))
