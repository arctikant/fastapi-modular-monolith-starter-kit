from aiocache import caches

from app.core.configs import app_config

caches.set_config(
    {
        'default': {
            'cache': 'aiocache.RedisCache',
            'endpoint': app_config.REDIS_HOST,
            'port': app_config.REDIS_PORT,
            'timeout': 1,
            'serializer': {'class': 'aiocache.serializers.PickleSerializer'},
        }
    }
)
cache_provider = caches.get('default')
