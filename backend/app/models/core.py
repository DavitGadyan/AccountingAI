"""Firm, users, clients, entities and the ownership graph."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, FirmScopedMixin, TimestampMixin, UUIDMixin
from app.models.enums import EntityType, TaxClassification, UserRole


class Firm(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "firms"

    name: Mapped[str] = mapped_column(String(200))
    ptin: Mapped[str | None] = mapped_column(String(20))
    efin: Mapped[str | None] = mapped_column(String(20))
    users: Mapped[list[User]] = relationship(back_populates="firm")


class User(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    __tablename__ = "users"

    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.PREPARER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Credential of record. A user without one cannot be assigned as signer — the check
    # lives in the filing gate, not in the UI.
    credential: Mapped[str | None] = mapped_column(String(40))  # "CPA", "EA", ...
    credential_number: Mapped[str | None] = mapped_column(String(60))
    credential_state: Mapped[str | None] = mapped_column(String(2))

    firm: Mapped[Firm] = relationship(back_populates="users")


class Client(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    __tablename__ = "clients"

    display_name: Mapped[str] = mapped_column(String(200))
    primary_contact_email: Mapped[str | None] = mapped_column(String(320))
    residence_country: Mapped[str] = mapped_column(String(2), default="CA")
    notes: Mapped[str | None] = mapped_column(Text)

    entities: Mapped[list[Entity]] = relationship(back_populates="client")


class Entity(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """Any node in the structure: the investor, the holdcos, the syndication LPs."""

    __tablename__ = "entities"

    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), index=True)
    name: Mapped[str] = mapped_column(String(250))
    entity_type: Mapped[EntityType] = mapped_column(String(40))
    tax_classification: Mapped[TaxClassification] = mapped_column(String(40))
    country: Mapped[str] = mapped_column(String(2), default="US")
    formation_state: Mapped[str | None] = mapped_column(String(2))

    us_tin: Mapped[str | None] = mapped_column(String(20))
    foreign_tin: Mapped[str | None] = mapped_column(String(30))

    # Treaty posture. Claiming a treaty rate without an LOB analysis is the single most
    # common defect in cross-border returns, so the analysis is a stored field.
    treaty_country: Mapped[str | None] = mapped_column(String(2))
    treaty_lob_qualified: Mapped[bool | None] = mapped_column(Boolean)
    treaty_lob_basis: Mapped[str | None] = mapped_column(Text)

    is_syndication: Mapped[bool] = mapped_column(Boolean, default=False)
    syndicator_name: Mapped[str | None] = mapped_column(String(200))
    first_investment_date: Mapped[date | None] = mapped_column(Date)
    exited_on: Mapped[date | None] = mapped_column(Date)

    # A §871(d)/§882(d) election, once made, binds later years. Stored on the entity so
    # every future year sees it without re-reading a prior return.
    net_election_871d: Mapped[bool] = mapped_column(Boolean, default=False)
    net_election_year: Mapped[int | None] = mapped_column()

    client: Mapped[Client] = relationship(back_populates="entities")
    property_states: Mapped[list[PropertyState]] = relationship(back_populates="entity")


class Ownership(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """A directed edge: ``owner_entity_id`` holds an interest in ``owned_entity_id``."""

    __tablename__ = "ownerships"
    __table_args__ = (
        UniqueConstraint("owner_entity_id", "owned_entity_id", "effective_from", name="uq_edge"),
    )

    owner_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    owned_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)

    # Profits and capital can diverge sharply in a syndication waterfall, and the two
    # percentages drive different rules, so both are stored.
    profits_pct: Mapped[float] = mapped_column(Numeric(9, 6))
    capital_pct: Mapped[float] = mapped_column(Numeric(9, 6))
    loss_pct: Mapped[float | None] = mapped_column(Numeric(9, 6))

    is_general_partner: Mapped[bool] = mapped_column(Boolean, default=False)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class PropertyState(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    """Where a syndication's real property actually sits — the state nexus driver."""

    __tablename__ = "property_states"

    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    state: Mapped[str] = mapped_column(String(2))
    property_name: Mapped[str | None] = mapped_column(String(200))
    apportionment_pct: Mapped[float | None] = mapped_column(Float)
    composite_election_made: Mapped[bool] = mapped_column(Boolean, default=False)
    withholding_remitted: Mapped[float | None] = mapped_column(Numeric(14, 2))

    entity: Mapped[Entity] = relationship(back_populates="property_states")


class Engagement(Base, UUIDMixin, TimestampMixin, FirmScopedMixin):
    __tablename__ = "engagements"
    __table_args__ = (UniqueConstraint("client_id", "tax_year", name="uq_client_year"),)

    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), index=True)
    tax_year: Mapped[int] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(30), default="onboarding")

    fixed_fee: Mapped[float | None] = mapped_column(Numeric(12, 2))
    fee_currency: Mapped[str] = mapped_column(String(3), default="USD")
    is_first_year: Mapped[bool] = mapped_column(Boolean, default=True)

    assigned_preparer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    assigned_reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))

    # Set by the rollforward service when a prior year exists. Year 2 of the same
    # structure should be a re-run, not a re-build.
    rolled_from_engagement_id: Mapped[str | None] = mapped_column(String(36))
