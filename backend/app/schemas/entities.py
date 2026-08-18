from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ClientCreate(BaseModel):
    display_name: str
    primary_contact_email: str | None = None
    residence_country: str = "CA"
    notes: str | None = None


class ClientOut(ORMModel):
    id: str
    display_name: str
    primary_contact_email: str | None
    residence_country: str
    notes: str | None


class EntityCreate(BaseModel):
    client_id: str
    name: str
    entity_type: str
    tax_classification: str
    country: str = "US"
    formation_state: str | None = None
    us_tin: str | None = None
    foreign_tin: str | None = None
    treaty_country: str | None = None
    treaty_lob_qualified: bool | None = None
    treaty_lob_basis: str | None = None
    is_syndication: bool = False
    syndicator_name: str | None = None
    first_investment_date: date | None = None


class EntityOut(ORMModel):
    id: str
    client_id: str
    name: str
    entity_type: str
    tax_classification: str
    country: str
    formation_state: str | None
    us_tin: str | None
    treaty_country: str | None
    treaty_lob_qualified: bool | None
    is_syndication: bool
    syndicator_name: str | None
    exited_on: date | None
    net_election_871d: bool


class OwnershipCreate(BaseModel):
    owner_entity_id: str
    owned_entity_id: str
    profits_pct: float = Field(ge=0, le=100)
    capital_pct: float = Field(ge=0, le=100)
    loss_pct: float | None = None
    is_general_partner: bool = False
    effective_from: date


class OwnershipOut(ORMModel):
    id: str
    owner_entity_id: str
    owned_entity_id: str
    profits_pct: float
    capital_pct: float
    is_general_partner: bool
    effective_from: date
    effective_to: date | None


class PropertyStateCreate(BaseModel):
    entity_id: str
    state: str = Field(min_length=2, max_length=2)
    property_name: str | None = None
    apportionment_pct: float | None = None
    composite_election_made: bool = False


class PropertyStateOut(ORMModel):
    id: str
    entity_id: str
    state: str
    property_name: str | None
    apportionment_pct: float | None
    composite_election_made: bool


class StructureNode(BaseModel):
    """One node in the org chart the UI renders."""

    id: str
    name: str
    entity_type: str
    country: str
    is_syndication: bool
    states: list[str] = Field(default_factory=list)
    k1_count: int = 0


class StructureEdge(BaseModel):
    source: str
    target: str
    profits_pct: float
    capital_pct: float


class StructureGraph(BaseModel):
    nodes: list[StructureNode]
    edges: list[StructureEdge]


class EngagementCreate(BaseModel):
    client_id: str
    tax_year: int = Field(ge=2020, le=2035)
    fixed_fee: float | None = None
    fee_currency: str = "USD"
    assigned_preparer_id: str | None = None
    assigned_reviewer_id: str | None = None


class EngagementOut(ORMModel):
    id: str
    client_id: str
    tax_year: int
    status: str
    fixed_fee: float | None
    fee_currency: str
    is_first_year: bool
    assigned_preparer_id: str | None
    assigned_reviewer_id: str | None


class EngagementDashboard(BaseModel):
    engagement: EngagementOut
    client_name: str
    documents_received: int
    documents_expected: int
    fields_needing_review: int
    determinations: int
    filings_required: int
    filings_accepted: int
    open_items_blocking: int
    open_items_total: int
    next_due_date: date | None
    memo_available: bool
