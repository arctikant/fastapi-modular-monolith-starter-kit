import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.db import get_session
from app.core.deps import logger

max_tries = 60 * 1  # 1 minutes
wait_seconds = 5


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),  # type: ignore
    after=after_log(logger, logging.INFO),  # type: ignore
)
async def init(db: AsyncSession) -> None:
    try:
        # Check if DB is awake
        await db.execute(select(1))
    except Exception as exc:
        await logger.a_exception('database_init_error')
        raise exc


async def main() -> None:
    await logger.a_info('app_initialization_started')
    async for db in get_session():
        await init(db)
        break
    await logger.a_info('app_initialization_finished')


if __name__ == '__main__':
    asyncio.run(main())
