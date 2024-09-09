from typing import Any

from aiocache import BaseCache

from app.core.services.cache.base_service import CacheServiceInterface


class AioCacheService(CacheServiceInterface):
    def __init__(self, cache: BaseCache) -> None:
        self._cache = cache

    async def get(self, key: str) -> Any | None:
        return await self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self._cache.set(key, value, ttl=ttl)

    async def delete(self, key: str) -> None:
        await self._cache.delete(key)
