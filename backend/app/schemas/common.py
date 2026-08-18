from __future__ import annotations

from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int = 50
    offset: int = 0


class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    email: str
    password: str


class CurrentUser(ORMModel):
    id: str
    firm_id: str
    email: str
    full_name: str
    role: str
    credential: str | None = None
    credential_number: str | None = None


class DueDates(BaseModel):
    original: date | None = None
    extended: date | None = None


class AuditEntry(ORMModel):
    id: str
    action: str
    object_type: str
    object_id: str | None
    summary: str
    actor_user_id: str | None
    created_at: datetime
    payload: dict = Field(default_factory=dict)
