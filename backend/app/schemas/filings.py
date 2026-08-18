from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class DeterminationOut(ORMModel):
    id: str
    entity_id: str
    rule_id: str
    rule_version: str
    form: str
    jurisdiction: str
    state: str | None
    requirement: str
    rationale: str
    authority: str
    triggering_facts: dict = Field(default_factory=dict)
    confidence: float
    due_date: date | None
    extended_due_date: date | None
    override_requirement: str | None
    override_reason: str | None


class DeterminationOverride(BaseModel):
    requirement: str
    reason: str = Field(min_length=20, description="Overrides without reasoning are not accepted")


class FilingOut(ORMModel):
    id: str
    entity_id: str
    form: str
    tax_year: int
    jurisdiction: str
    state: str | None
    status: str
    is_protective: bool
    is_extension: bool
    # Who signed and when. The client's deliverable list includes filing confirmations,
    # and a confirmation that does not name the signer is half a record.
    prepared_at: datetime | None
    approved_by_id: str | None
    approved_at: datetime | None
    submission_id: str | None
    transmitted_at: datetime | None
    acknowledged_at: datetime | None
    ack_reference: str | None
    reject_codes: list | None
    balance_due: float | None


class FilingApproval(BaseModel):
    attestation: bool = Field(
        description="Signer confirms they have reviewed the return and supporting workpapers"
    )
    note: str | None = None


class TransmitResult(BaseModel):
    filing_id: str
    submission_id: str
    accepted: bool
    reference: str
    transmitted_at: datetime


class GateCheck(BaseModel):
    filing_id: str
    transmittable: bool
    blockers: list[str]


class WorkpaperOut(ORMModel):
    id: str
    entity_id: str | None
    code: str
    title: str
    rows: list = Field(default_factory=list)
    totals: dict = Field(default_factory=dict)
    narrative: str | None
    ties_out: bool
    tie_out_detail: dict = Field(default_factory=dict)


class OpenItemOut(ORMModel):
    id: str
    entity_id: str | None
    code: str
    title: str
    detail: str
    severity: str
    status: str
    blocks_filing: bool
    requested_from: str | None
    resolution_note: str | None


class OpenItemUpdate(BaseModel):
    status: str
    resolution_note: str | None = None


class VarianceOut(ORMModel):
    id: str
    entity_id: str | None
    metric: str
    prior_year: int
    prior_value: float | None
    current_value: float | None
    absolute_change: float | None
    relative_change: float | None
    is_material: bool
    explanation: str | None


class PipelineReportOut(BaseModel):
    engagement_id: str
    tax_year: int
    rules_evaluated: int
    determinations: int
    filings_required: int
    workpapers_generated: int
    open_items: int
    blocking_items: int
    variances: int


class MemoOut(BaseModel):
    engagement_id: str
    markdown: str


class DeliverableOut(ORMModel):
    id: str
    engagement_id: str
    storage_key: str
    manifest: dict = Field(default_factory=dict)
    released_at: datetime | None
