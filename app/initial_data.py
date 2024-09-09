import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.config import auth_config
from app.auth.models.user import User, UserStatus
from app.auth.repositories.user import UserRepository
from app.auth.schemas.user import UserCreate
from app.core.db import get_session
from app.core.deps import logger


async def create_first_user(db: AsyncSession) -> None:
    user_repository = UserRepository(User)

    user = await user_repository.get_by_email(db=db, email=auth_config.FIRST_USER_EMAIL)
    if not user:
        user_data = UserCreate(
            username='Admin',
            email=auth_config.FIRST_USER_EMAIL,
            password=auth_config.FIRST_USER_PASSWORD,
            status_id=UserStatus.ACTIVE,
        )
        await user_repository.create(db=db, data=user_data)
        await user_repository.commit(db=db)


async def main() -> None:
    await logger.a_info('database_seeding_started')
    async for db in get_session():
        await create_first_user(db)
        break
    await logger.a_info('database_seeding_finished')


if __name__ == '__main__':
    asyncio.run(main())
