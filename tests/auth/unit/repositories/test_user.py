import pytest
from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from app.auth.models.user import User, UserStatus
from app.auth.repositories.user import UserRepository
from app.auth.schemas.user import UserCreate, UserUpdate
from app.auth.security import verify_hash
from app.core.db.exceptions import DatabaseException
from tests.factories.user import UserFactory


class TestUserRepository:
    # Fixtures

    @pytest.fixture(scope='class')
    def repo(self) -> UserRepository:
        return UserRepository(User)

    @pytest.fixture(autouse=True)
    def init_factories(self, db: AsyncSession) -> None:
        UserFactory._meta.sqlalchemy_session = db

    # Tests

    async def test_get_by_email(self, db: AsyncSession, repo: UserRepository) -> None:
        user = await UserFactory.create()

        retrieved = await repo.get_by_email(db=db, email=user.email)

        assert retrieved
        assert retrieved.id == user.id
        assert retrieved.email == user.email

    async def test_create(self, db: AsyncSession, faker: Faker, repo: UserRepository) -> None:
        # Can create
        user_data = UserCreate(
            email=faker.email(),
            username=faker.user_name(),
            password=faker.password(),
        )
        await repo.create(db=db, data=user_data)
        await repo.commit(db)

        result = await db.execute(select(User).where(User.email == user_data.email))  # type: ignore
        created = result.scalars().first()

        assert created
        assert created.email == user_data.email
        assert created.username == user_data.username
        assert verify_hash(data=user_data.password, hashed_data=created.password_hash)  # type: ignore[arg-type]

        # Can't create duplicate
        with pytest.raises(DatabaseException, match='Database error occurred'):
            await repo.create(db=db, data=user_data)
            await repo.commit(db)

        result = await db.execute(select(count()).select_from(User).where(User.email == user_data.email))  # type: ignore
        assert result.scalar_one() == 1

    async def test_update(self, db: AsyncSession, faker: Faker, repo: UserRepository) -> None:
        user = await UserFactory.create()

        user_data = UserUpdate(
            email=faker.email(),
            username=faker.user_name(),
            password=faker.password(),
            status_id=UserStatus.INACTIVE,
        )
        await repo.update(db=db, model=user, data=user_data)
        await repo.commit(db)

        updated = await db.get(User, user.id)

        assert updated
        assert updated.id == user.id
        assert updated.email == user.email
        assert updated.username == user.username
        assert updated.status_id == UserStatus.INACTIVE.value
        assert verify_hash(data=user_data.password, hashed_data=updated.password_hash)  # type: ignore[arg-type]

    async def test_authenticate(self, db: AsyncSession, repo: UserRepository, faker: Faker) -> None:
        user = await UserFactory.create()
        password = UserFactory.get_password()

        # Can authenticate
        authenticated = await repo.authenticate(db=db, email=user.email, password=password)

        assert authenticated
        assert authenticated.id == user.id

        # Can't authenticate with wrong password
        not_authenticated = await repo.authenticate(db=db, email=user.email, password=faker.password())

        assert not_authenticated is None

        # Can't authenticate with not existing email
        not_found = await repo.authenticate(db=db, email=faker.email(), password=password)

        assert not_found is None
