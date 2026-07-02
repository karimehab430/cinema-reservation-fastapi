from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.exceptions import AuthenticationError, ConflictError, InvalidTokenError, NotFoundError
from app.models import RefreshToken, User, UserRole
from app.schemas import RefreshRequest, TokenPair, UserCreate
from app.services.users import UserService

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def register(self, payload: UserCreate) -> User:
        if await self.user_service.get_by_email(str(payload.email)):
            raise ConflictError("Email already registered")

        user = User(
            email=str(payload.email),
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=UserRole.USER.value,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        logger.info("user_registered", extra={"event": "user_registered", "user_id": str(user.id)})
        return user

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self.user_service.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning("login_failed", extra={"event": "login_failed", "email": email})
            raise AuthenticationError("Incorrect email or password")

        token_pair = await self._issue_tokens(user)
        logger.info("login_succeeded", extra={"event": "login_succeeded", "user_id": str(user.id)})
        return token_pair

    async def refresh_token(self, payload: RefreshRequest) -> TokenPair:
        try:
            data = decode_token(payload.refresh_token)
            if data.get("type") != "refresh":
                raise ValueError("invalid type")
            user_id = uuid.UUID(str(data["sub"]))
        except (KeyError, ValueError, TypeError) as exc:
            raise InvalidTokenError("Invalid refresh token") from exc

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        )
        stored_tokens = result.scalars().all()

        matched = next((token for token in stored_tokens if verify_password(payload.refresh_token, token.hashed_token)), None)
        if matched is None or matched.expires_at < datetime.now(timezone.utc):
            raise InvalidTokenError("Refresh token expired or revoked")

        matched.revoked = True
        await self.db.commit()

        user = await self.db.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found")
        return await self._issue_tokens(user)

    async def _issue_tokens(self, user: User) -> TokenPair:
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

        self.db.add(
            RefreshToken(
                user_id=user.id,
                hashed_token=hash_password(refresh_token),
                expires_at=expires_at,
            )
        )
        await self.db.commit()
        return TokenPair(access_token=access_token, refresh_token=refresh_token)
