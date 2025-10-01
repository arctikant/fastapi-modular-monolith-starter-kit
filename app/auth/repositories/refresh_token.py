from sqlalchemy import delete, select
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
    async def upsert(self, data: RefreshTokenBase, model: RefreshToken | None = None) -> RefreshToken:
        if not model:
            result = await self._db.execute(select(RefreshToken).where(RefreshToken.user_id == data.user_id))  # type: ignore
            model = result.scalars().first()

        if model:
            return await self.update(
                model=model,
                data=RefreshTokenUpdate(
                    token=self._get_prefix(data.token), hash=generate_hash(data.token), expires_at=data.expires_at
                ),
            )
        else:
            return await self.create(
                data=RefreshTokenCreate(
                    token=self._get_prefix(data.token),
                    hash=generate_hash(data.token),
                    expires_at=data.expires_at,
                    user_id=data.user_id,
                ),
            )

    async def get_with_user(self, token: str) -> RefreshToken | None:
        result = await self._db.execute(
            select(RefreshToken)
            .options(selectinload(RefreshToken.user))
            .where(RefreshToken.token == self._get_prefix(token))
        )
        return result.unique().scalar_one_or_none()

    async def delete_by_user_id(self, user_id: int) -> None:
        await self._db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))

    def _get_prefix(self, token: str) -> str:
        return token[:24]
