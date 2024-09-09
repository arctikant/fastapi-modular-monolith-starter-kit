from collections.abc import AsyncGenerator

import pytest
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import User
from app.core.configs import app_config
from app.core.db.session import engine
from app.core.models import BaseModel
from app.main import app


@pytest.fixture(scope='session')
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    assert app_config.ENVIRONMENT == 'testing'

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield engine

    await engine.dispose()
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest.fixture
async def db(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session
        await session.execute(delete(RefreshToken))
        await session.execute(delete(User))
        # Add here tables to refresh for each test
        await session.commit()


@pytest.fixture(scope='session')
def faker() -> Faker:
    return Faker()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=app_config.app_url) as client:
        yield client
