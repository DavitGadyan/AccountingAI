"""Declarative base and the mixins every table shares."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class UUIDMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=lambda: datetime.now(UTC),
    )


class FirmScopedMixin:
    """Tenant key.

    Every query in the API layer filters on this. It is not optional and it is not
    enforced only in the UI — see ``app.api.deps.firm_scoped``.
    """

    firm_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
