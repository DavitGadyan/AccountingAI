from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import SessionDep, UserDep
from app.core.config import settings
from app.core.errors import PermissionDenied
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas.common import CurrentUser, LoginRequest, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, session: SessionDep) -> TokenPair:
    user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    # Same response for unknown email and wrong password — anything else enumerates users.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise PermissionDenied("Invalid email or password").as_http()
    if not user.is_active:
        raise PermissionDenied("Invalid email or password").as_http()

    return TokenPair(
        access_token=create_access_token(user.id, firm_id=user.firm_id, role=str(user.role)),
        expires_in=settings.access_token_minutes * 60,
    )


@router.get("/me", response_model=CurrentUser)
async def me(user: UserDep) -> CurrentUser:
    return CurrentUser.model_validate(user)
