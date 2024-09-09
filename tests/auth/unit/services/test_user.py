from unittest.mock import Mock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from app.auth.exceptions import InvalidInput
from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import User
from app.auth.schemas.user import UserUpdate
from app.auth.services.user import UserService
from app.core.db import ListParams, PaginatedResult, Pagination
from tests.auth.factories.refresh_token import RefreshTokenFactory
from tests.factories.user import UserFactory


class TestUserService:
    # Fixtures

    @pytest.fixture
    def mock_event_service(self) -> Mock:
        return Mock()

    @pytest.fixture
    def user_service(self, db: AsyncSession, mock_event_service: Mock) -> UserService:
        return UserService(db=db, events=mock_event_service)

    @pytest.fixture(autouse=True)
    def init_factories(self, db: AsyncSession) -> None:
        UserFactory._meta.sqlalchemy_session = db
        RefreshTokenFactory._meta.sqlalchemy_session = db

    # Tests

    async def test_get_list(self, db: AsyncSession, user_service: UserService) -> None:
        await UserFactory.create_batch(3)
        retrieved: PaginatedResult[User] = await user_service.get_list(params=ListParams())  # type: ignore[call-arg]

        assert isinstance(retrieved, PaginatedResult)
        assert retrieved.pagination and isinstance(retrieved.pagination, Pagination)
        assert retrieved.items and len(retrieved.items) > 1

    async def test_get(self, db: AsyncSession, user_service: UserService) -> None:
        users = await UserFactory.create_batch(3)
        retrieved = await user_service.get(users[1].id)

        assert isinstance(retrieved, User)
        assert retrieved.id == users[1].id

    async def test_update(self, db: AsyncSession, user_service: UserService) -> None:
        users = await UserFactory.create_batch(2)
        new_username = 'new_username'
        user_data = UserUpdate(username=new_username)

        await user_service.update(users[0], user_data)

        updated = await db.get(User, users[0].id)
        assert updated and updated.username == new_username

        # Check that can change email to existing one
        user_data = UserUpdate(email=users[1].email)

        with pytest.raises(InvalidInput, match="Can't update user with provided data"):
            await user_service.update(users[0], user_data)

    async def test_delete(self, db: AsyncSession, user_service: UserService) -> None:
        refresh_token = await RefreshTokenFactory.create(user=await UserFactory.create())

        with pytest.raises(InvalidInput, match='Either user_id or user must be provided'):
            await user_service.delete()

        await user_service.delete(user_id=refresh_token.user_id)

        deleted_user = await db.get(User, refresh_token.user_id)
        deleted_token = await db.execute(
            select(count()).select_from(RefreshToken).where(RefreshToken.user_id == refresh_token.user_id)
        )

        assert deleted_user and deleted_user.is_deleted()
        assert deleted_token.scalar_one() == 0

        refresh_token = await RefreshTokenFactory.create(user=await UserFactory.create())
        await user_service.delete(user=refresh_token.user)

        deleted_user = await db.get(User, refresh_token.user_id)
        deleted_token = await db.execute(
            select(count()).select_from(RefreshToken).where(RefreshToken.user_id == refresh_token.user_id)
        )

        assert deleted_user and deleted_user.is_deleted()
        assert deleted_token.scalar_one() == 0
