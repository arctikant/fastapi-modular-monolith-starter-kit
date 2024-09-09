from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import User
from app.auth.repositories.refresh_token import RefreshTokenRepository
from app.auth.schemas.token import RefreshTokenBase
from app.auth.security import generate_refresh_token, verify_hash
from tests.auth.factories.refresh_token import RefreshTokenFactory
from tests.factories.user import UserFactory


class TestRefreshTokenRepository:
    # Fixtures

    @pytest.fixture(scope='class')
    def repo(self) -> RefreshTokenRepository:
        return RefreshTokenRepository(RefreshToken)

    @pytest.fixture(autouse=True)
    def init_factories(self, db: AsyncSession) -> None:
        UserFactory._meta.sqlalchemy_session = db
        RefreshTokenFactory._meta.sqlalchemy_session = db

    # Tests

    async def test_upsert(self, db: AsyncSession, repo: RefreshTokenRepository) -> None:
        user = await UserFactory.create()

        # Can insert
        insert_data = RefreshTokenBase(
            token=generate_refresh_token(),
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        await repo.upsert(db=db, data=insert_data)
        await repo.commit(db)

        inserted = await db.get(RefreshToken, insert_data.token[:24])

        assert inserted
        assert inserted.user_id == user.id
        assert inserted.expires_at == insert_data.expires_at
        assert inserted.token == insert_data.token[:24]
        assert verify_hash(data=insert_data.token, hashed_data=inserted.hash)

        # Can update
        update_data = RefreshTokenBase(
            token=generate_refresh_token(),
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(days=3),
        )
        await repo.upsert(db=db, data=update_data, model=inserted)
        await repo.commit(db)

        result = await db.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))  # type: ignore
        updated = result.scalars().all()

        assert len(updated) == 1
        assert updated[0]
        assert updated[0].user_id == user.id
        assert updated[0].expires_at == update_data.expires_at
        assert updated[0].token == update_data.token[:24]
        assert verify_hash(data=update_data.token, hashed_data=updated[0].hash)

    async def test_get_with_user(self, db: AsyncSession, repo: RefreshTokenRepository) -> None:
        refresh_token = await RefreshTokenFactory.create(user=await UserFactory.create())

        retrieved = await repo.get_with_user(db=db, token=refresh_token.token)

        assert retrieved
        assert isinstance(retrieved.user, User)
        assert retrieved.user.id == refresh_token.user_id

    async def test_delete_by_user_id(self, db: AsyncSession, repo: RefreshTokenRepository) -> None:
        refresh_token = await RefreshTokenFactory.create(user=await UserFactory.create())

        result = await db.execute(
            select(count()).select_from(RefreshToken).where(RefreshToken.user_id == refresh_token.user_id)
        )  # type: ignore
        assert result.scalar_one() == 1

        await repo.delete_by_user_id(db=db, user_id=refresh_token.user_id)

        result = await db.execute(
            select(count()).select_from(RefreshToken).where(RefreshToken.user_id == refresh_token.user_id)
        )  # type: ignore
        assert result.scalar_one() == 0
