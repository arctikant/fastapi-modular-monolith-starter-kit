import hashlib
import json
from collections.abc import Callable
from functools import wraps

from aiocache import BaseCache


class AioCachedDecorator:
    def __init__(self, cache: BaseCache) -> None:
        self._cache = cache

    def __call__(self, ttl: int, key_builder: Callable | None = None) -> Callable:
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Build cache key
                cache_key = (
                    key_builder(func, *args, **kwargs) if key_builder else self._build_key(func, *args, **kwargs)
                )

                # Try to get cached result
                cached_value = await self._cache.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # If not cached, call the function and cache the result
                result = await func(*args, **kwargs)
                await self._cache.set(key=cache_key, value=result, ttl=ttl)
                return result

            return wrapper

        return decorator

    def _build_key(self, func: Callable, *args, **kwargs) -> str:
        # Combine function name, args, and kwargs into a single dictionary
        key_data = {'func': func.__name__, 'args': args, 'kwargs': kwargs}

        # Convert the dictionary to a JSON string and create a hash
        json_str = json.dumps(key_data, sort_keys=True)
        hash_str = hashlib.md5(json_str.encode()).hexdigest()

        return f'{func.__name__}:{hash_str}'
