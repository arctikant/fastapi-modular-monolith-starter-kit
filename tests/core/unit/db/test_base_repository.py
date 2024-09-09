import pytest
from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from app.auth import UserDTO
from app.auth.models.user import User
from app.auth.schemas.user import UserCreate, UserUpdate
from app.core.db import (
    BaseRepository,
    FilterParam,
    ListParams,
    PaginatedResult,
    Pagination,
    SortOrder,
    SortParam,
)
from tests.factories.user import UserFactory


class StubRepository(BaseRepository[User, UserCreate, UserUpdate]):
    pass


class TestBaseRepository:
    # Fixtures

    @pytest.fixture(scope='class')
    def repo(self) -> StubRepository:
        return StubRepository(User)

    @pytest.fixture(autouse=True)
    def init_factories(self, db: AsyncSession) -> None:
        UserFactory._meta.sqlalchemy_session = db

    # Tests

    async def test_get(self, db: AsyncSession, repo: StubRepository) -> None:
        user = await UserFactory.create()

        retrieved = await repo.get(db=db, model_id=user.id)

        assert retrieved
        assert isinstance(retrieved, User)
        assert retrieved.id == user.id

        # Check soft delete
        await repo.delete(db=db, model_id=user.id)
        await repo.commit(db)

        retrieved = await repo.get(db=db, model_id=user.id)
        assert not retrieved

        retrieved = await repo.get(db=db, model_id=user.id, with_deleted=True)
        assert retrieved

    async def test_get_list(self, db: AsyncSession, repo: StubRepository) -> None:
        # Seed users
        users = await UserFactory.create_batch(3)

        # Check general structure
        params = ListParams(page=1, per_page=2)  # type: ignore[call-arg]
        retrieved = await repo.get_list(db=db, params=params)

        assert retrieved and isinstance(retrieved, PaginatedResult)
        assert retrieved.items and isinstance(retrieved.items, list)
        assert retrieved.pagination and isinstance(retrieved.pagination, Pagination)
        assert len(retrieved.items) == 2
        assert retrieved.pagination.total == 3
        assert retrieved.pagination.page == 1
        assert retrieved.pagination.per_page == 2
        assert isinstance(retrieved.items[0], User)

        # Check schema conversation
        retrieved = await repo.get_list(db=db, params=params, schema=UserDTO)
        assert isinstance(retrieved.items[0], UserDTO)

        # Check sorting
        params = ListParams(sort=[SortParam(field='id', order=SortOrder.asc)])  # type: ignore[call-arg]
        retrieved = await repo.get_list(db=db, params=params)

        assert retrieved.items[0].id < retrieved.items[1].id

        params = ListParams(sort=[SortParam(field='id', order=SortOrder.desc)])  # type: ignore[call-arg]
        retrieved = await repo.get_list(db=db, params=params)

        assert retrieved.items[0].id > retrieved.items[1].id

        # Check pagination
        params = ListParams(sort=[SortParam(field='id', order=SortOrder.asc)], page=1, per_page=1)  # type: ignore[call-arg]
        first = await repo.get_list(db=db, params=params)

        params.page = 2
        second = await repo.get_list(db=db, params=params)

        assert first.pagination.page == 1
        assert second.pagination.page == 2
        assert first.items[0].id < second.items[0].id

        # Check filter
        params = ListParams(filters=[FilterParam(field='id', value=users[0].id)])  # type: ignore[call-arg]
        retrieved = await repo.get_list(db=db, params=params)

        assert len(retrieved.items) == 1
        assert retrieved.pagination.total == 1
        assert retrieved.items[0].id == users[0].id

        params = ListParams(
            filters=[FilterParam(field='id', value=[users[0].id, users[1].id])],
            sort=[SortParam(field='id', order=SortOrder.asc)],
        )  # type: ignore[call-arg]
        retrieved = await repo.get_list(db=db, params=params)

        assert len(retrieved.items) == 2
        assert retrieved.pagination.total == 2
        assert retrieved.items[0].id == users[0].id
        assert retrieved.items[1].id == users[1].id

        # Check soft delete
        await repo.delete(db=db, model_id=users[0].id)
        await repo.commit(db)

        params = ListParams(page=1, per_page=10)  # type: ignore[call-arg]
        retrieved = await repo.get_list(db=db, params=params)

        assert len(retrieved.items) == 2
        assert retrieved.pagination.total == 2

        retrieved = await repo.get_list(db=db, params=params, with_deleted=True)

        assert len(retrieved.items) == 3
        assert retrieved.pagination.total == 3

    async def test_create(self, db: AsyncSession, repo: StubRepository, faker: Faker) -> None:
        # Can create
        user_data = UserCreate(
            email=faker.email(),
            username=faker.user_name(),
            password_hash=faker.password(),
        )
        await repo.create(db=db, data=user_data)
        await repo.commit(db)

        result = await db.execute(select(User).where(User.email == user_data.email))  # type: ignore
        created = result.scalars().first()

        assert created
        assert isinstance(created, User)

    async def test_update(self, db: AsyncSession, repo: StubRepository, faker: Faker) -> None:
        user = await UserFactory.create()

        user_data = UserUpdate(email=faker.email())
        await repo.update(db=db, model=user, data=user_data)
        await repo.commit(db)

        updated = await db.get(User, user.id)

        assert updated
        assert updated.id == user.id
        assert updated.email == user.email

    async def test_delete(self, db: AsyncSession, repo: StubRepository) -> None:
        user = await UserFactory.create()

        await repo.delete(db=db, model_id=user.id)
        await repo.commit(db)

        # Check that user was soft deleted
        result = await db.execute(
            select(count()).select_from(User).where(User.id == user.id).where(User.deleted_at.isnot(None))
        )
        assert result.scalar_one() == 1

        await repo.delete(db=db, model_id=user.id, is_soft=False)
        await repo.commit(db)

        # Check that user deleted from DB completely
        result = await db.execute(select(count()).select_from(User).where(User.id == user.id))
        assert result.scalar_one() == 0

    async def test_delete_all(self, db: AsyncSession, repo: StubRepository) -> None:
        users = await UserFactory.create_batch(3)
        ids = [user.id for user in users]

        result = await db.execute(select(count()).select_from(User).where(User.id.in_(ids)))
        assert result.scalar_one() == 3

        await repo.delete_all(db=db, model_ids=ids)

        result = await db.execute(select(count()).select_from(User).where(User.id.in_(ids)))
        assert result.scalar_one() == 0

    async def test_commit(self, db: AsyncSession, repo: StubRepository, faker: Faker) -> None:
        user_data = UserCreate(
            email=faker.email(),
            username=faker.user_name(),
            password_hash=faker.password(),
        )
        await repo.create(db=db, data=user_data)

        result = await db.execute(select(count()).select_from(User).where(User.email == user_data.email))  # type: ignore
        assert result.scalar_one() == 0

        await repo.commit(db)

        result = await db.execute(select(User).where(User.email == user_data.email))  # type: ignore
        created = result.scalars().first()

        assert created
        assert isinstance(created, User)
