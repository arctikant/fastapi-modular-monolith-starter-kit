from typing import Any

from app.core.services.cache.base_service import CacheServiceInterface
from app.core.services.cache.providers.aiocache.decorators import AioCachedDecorator
from app.core.services.cache.providers.aiocache.service import AioCacheService
from app.core.services.cache.providers.aiocache.setup import cache_provider


def get_cache_service() -> CacheServiceInterface:
    return AioCacheService(cache_provider)


def get_cached_decorator() -> Any:
    return AioCachedDecorator(cache_provider)
