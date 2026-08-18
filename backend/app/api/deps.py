"""Request dependencies.

``firm_scoped`` is the tenancy boundary. Every router that touches firm data takes it,
and every query filters on the firm id it returns — never on a value from the request
body, which is the shape that produces cross-tenant reads.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, PermissionDenied
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models import Engagement, User
from app.models.enums import UserRole

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def current_user(
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise PermissionDenied("Missing bearer token").as_http()
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except PermissionDenied as exc:
        raise exc.as_http() from exc

    user = await session.get(User, payload.get("sub", ""))
    if user is None or not user.is_active:
        raise PermissionDenied("User is not active").as_http()
    return user


UserDep = Annotated[User, Depends(current_user)]


async def firm_scoped(user: UserDep) -> str:
    return user.firm_id


FirmDep = Annotated[str, Depends(firm_scoped)]


def require_role(*roles: UserRole):
    async def _dep(user: UserDep) -> User:
        if user.role not in roles:
            raise PermissionDenied(
                f"This action requires one of: {', '.join(roles)}. "
                f"You hold '{user.role}'."
            ).as_http()
        return user

    return _dep


ReviewerDep = Annotated[User, Depends(require_role(UserRole.REVIEWER, UserRole.ADMIN))]
StaffDep = Annotated[
    User, Depends(require_role(UserRole.REVIEWER, UserRole.ADMIN, UserRole.PREPARER))
]


async def get_engagement(engagement_id: str, session: SessionDep, firm_id: FirmDep) -> Engagement:
    engagement = await session.scalar(
        select(Engagement).where(
            Engagement.id == engagement_id, Engagement.firm_id == firm_id
        )
    )
    if engagement is None:
        # Deliberately identical to a genuine 404: a different message for "exists but
        # belongs to another firm" is itself a cross-tenant information leak.
        raise NotFound("Engagement not found").as_http()
    return engagement


EngagementDep = Annotated[Engagement, Depends(get_engagement)]
