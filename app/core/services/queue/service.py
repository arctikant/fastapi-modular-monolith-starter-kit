from typing import Any

from app.core.services.queue.base_service import QueueServiceInterface
from app.core.services.queue.providers.taskiq.decorators import TaskiqQueuedDecorator
from app.core.services.queue.providers.taskiq.service import TaskiqQueueService
from app.core.services.queue.providers.taskiq.setup import broker


def get_queue_service() -> QueueServiceInterface:
    return TaskiqQueueService(broker)


def get_queued_decorator() -> Any:
    return TaskiqQueuedDecorator(broker)
