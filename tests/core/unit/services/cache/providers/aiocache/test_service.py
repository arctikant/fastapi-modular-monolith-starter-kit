from unittest.mock import AsyncMock

import pytest

from app.core.services.cache.providers.aiocache.service import AioCacheService


class TestAioCacheService:
    # Fixtures

    @pytest.fixture
    def mock_cache(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def cache_service(self, mock_cache: AsyncMock) -> AioCacheService:
        return AioCacheService(mock_cache)

    # Tests

    async def test_get(self, mock_cache: AsyncMock, cache_service: AioCacheService) -> None:
        await cache_service.get('key')

        mock_cache.get.assert_called_once_with('key')

    async def test_set(self, mock_cache: AsyncMock, cache_service: AioCacheService) -> None:
        await cache_service.set(key='key', value='value', ttl=10)

        mock_cache.set.assert_called_once_with('key', 'value', ttl=10)

    async def test_delete(self, mock_cache: AsyncMock, cache_service: AioCacheService) -> None:
        await cache_service.delete('key')

        mock_cache.delete.assert_called_once_with('key')
