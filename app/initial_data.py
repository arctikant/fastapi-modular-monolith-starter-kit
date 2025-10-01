import asyncio

from app.auth import UserRepo
from app.auth.config import auth_config
from app.auth.dependencies.repositories import get_user_repository
from app.auth.models.user import UserStatus
from app.auth.schemas.user import UserCreate
from app.core.db import get_session
from app.core.deps import logger


async def create_first_user(user_repo: UserRepo) -> None:
    user = await user_repo.get_by_email(auth_config.FIRST_USER_EMAIL)
    if not user:
        user_data = UserCreate(
            username='Admin',
            email=auth_config.FIRST_USER_EMAIL,
            password=auth_config.FIRST_USER_PASSWORD,
            status_id=UserStatus.ACTIVE,
        )
        await user_repo.create(user_data)
        await user_repo.commit()


async def main() -> None:
    await logger.a_info('database_seeding_started')
    async for db in get_session():
        await create_first_user(get_user_repository(db))
        break
    await logger.a_info('database_seeding_finished')


if __name__ == '__main__':
    asyncio.run(main())
