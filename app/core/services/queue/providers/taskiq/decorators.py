from taskiq import AsyncBroker

from app.core.services.queue.base_task import BaseTask


class TaskiqQueuedDecorator:
    def __init__(self, broker: AsyncBroker) -> None:
        self._broker = broker

    def __call__(self, cls: type[BaseTask]) -> type[BaseTask]:
        self._broker.register_task(func=cls().run, task_name=cls.get_name())

        return cls
