from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class DocumentOut(ORMModel):
    id: str
    engagement_id: str
    filename: str
    kind: str
    kind_confidence: float | None
    status: str
    tax_year: int | None
    byte_size: int
    page_count: int | None
    sha256: str
    is_amended: bool
    source_entity_id: str | None
    recipient_entity_id: str | None
    created_at: datetime


class ExtractedFieldOut(ORMModel):
    id: str
    document_id: str
    field_path: str
    label: str
    raw_value: str | None
    numeric_value: float | None
    corrected_value: float | None
    confidence: float
    page: int | None
    source_text: str | None
    status: str


class FieldReviewRequest(BaseModel):
    """A reviewer either confirms the extracted value or replaces it."""

    confirmed: bool
    corrected_value: float | None = None
    note: str | None = None


class ExtractionSummary(BaseModel):
    document_id: str
    total_fields: int
    auto_accepted: int
    needs_review: int
    confirmed: int
    corrected: int
    auto_accept_rate: float
    model: str
    prompt_version: str


class K1RecordOut(ORMModel):
    id: str
    engagement_id: str
    partnership_entity_id: str
    partner_entity_id: str
    tax_year: int
    is_final_k1: bool
    is_amended: bool
    partnership_ein: str | None
    boxes: dict = Field(default_factory=dict)
    capital_account: dict = Field(default_factory=dict)
    liabilities: dict = Field(default_factory=dict)
    k3: dict = Field(default_factory=dict)
    state_amounts: dict = Field(default_factory=dict)
    withholding_1446: float | None
    reviewed_at: datetime | None
