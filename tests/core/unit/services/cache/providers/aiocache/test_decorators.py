import hashlib
import json
from unittest.mock import AsyncMock

import pytest

from app.core.services.cache.providers.aiocache.decorators import AioCachedDecorator


class TestAioCachedDecorator:
    # Fixtures

    @pytest.fixture
    def mock_cache(self) -> AsyncMock:
        return AsyncMock()

    # Tests

    async def test_call(self, mock_cache: AsyncMock) -> None:
        cached = AioCachedDecorator(mock_cache)
        mock_inner_function = AsyncMock(return_value='result')

        @cached(ttl=1, key_builder=lambda f, *args, **kwargs: f"{kwargs['key1']}:{kwargs['key2']}")
        async def test_function(key1: int, key2: int) -> str:
            return await mock_inner_function(key1, key2)

        mock_cache.get.return_value = None
        res = await test_function(key1=1, key2=2)

        assert res == 'result'
        mock_cache.get.assert_called_once_with('1:2')
        mock_cache.set.assert_called_once_with(key='1:2', value='result', ttl=1)

        mock_cache.reset_mock()
        mock_inner_function.reset_mock()
        mock_cache.get.return_value = 'new_result'
        res = await test_function(key1=1, key2=2)

        assert res == 'new_result'
        mock_cache.get.assert_called_once_with('1:2')
        mock_cache.set.assert_not_called()
        mock_inner_function.assert_not_called()

        @cached(ttl=1)
        async def test_function2(key1: int, key2: int) -> str:
            return await mock_inner_function(key1, key2)

        mock_cache.reset_mock()
        await test_function2(key1=1, key2=2)

        # Generate key
        key_data = {
            'func': 'test_function2',
            'args': (),
            'kwargs': {'key1': 1, 'key2': 2},
        }
        json_str = json.dumps(key_data, sort_keys=True)
        hash_str = hashlib.md5(json_str.encode()).hexdigest()

        mock_cache.get.assert_called_once_with(f'test_function2:{hash_str}')
