from taskiq import AsyncBroker, InMemoryBroker
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

from app.core.configs import app_config

broker: AsyncBroker

if app_config.ENVIRONMENT == 'testing':
    broker = InMemoryBroker()
else:
    broker = ListQueueBroker(url=app_config.QUEUE_REDIS_BROKER_URL)
    broker.with_result_backend(RedisAsyncResultBackend(app_config.QUEUE_REDIS_RESULT_BACKEND))
