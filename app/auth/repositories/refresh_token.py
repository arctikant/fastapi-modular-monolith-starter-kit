from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models.refresh_token import RefreshToken
from app.auth.schemas.token import (
    RefreshTokenBase,
    RefreshTokenCreate,
    RefreshTokenUpdate,
)
from app.auth.security import generate_hash
from app.core.db import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken, RefreshTokenCreate, RefreshTokenUpdate]):
    async def upsert(self, db: AsyncSession, data: RefreshTokenBase, model: RefreshToken | None = None) -> RefreshToken:
        if not model:
            result = await db.execute(select(RefreshToken).where(RefreshToken.user_id == data.user_id))  # type: ignore
            model = result.scalars().first()

        if model:
            return await self.update(
                db=db,
                model=model,
                data=RefreshTokenUpdate(
                    token=self._get_prefix(data.token), hash=generate_hash(data.token), expires_at=data.expires_at
                ),
            )
        else:
            return await self.create(
                db=db,
                data=RefreshTokenCreate(
                    token=self._get_prefix(data.token),
                    hash=generate_hash(data.token),
                    expires_at=data.expires_at,
                    user_id=data.user_id,
                ),
            )

    async def get_with_user(self, db: AsyncSession, token: str) -> RefreshToken | None:
        result = await db.execute(
            select(RefreshToken)
            .options(selectinload(RefreshToken.user))
            .where(RefreshToken.token == self._get_prefix(token))
        )
        return result.unique().scalar_one_or_none()

    async def delete_by_user_id(self, db: AsyncSession, user_id: int) -> None:
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))

    def _get_prefix(self, token: str) -> str:
        return token[:24]


refresh_token_repository = RefreshTokenRepository(RefreshToken)
