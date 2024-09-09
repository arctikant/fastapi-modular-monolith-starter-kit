from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.configs import app_config

engine = create_async_engine(
    str(app_config.postgres_url),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=app_config.SQL_ECHO,
    future=True,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
