from taskiq import AsyncBroker

from app.core.services.queue.base_task import BaseTask


class TaskiqQueuedDecorator:
    def __init__(self, broker: AsyncBroker) -> None:
        self._broker = broker

    def __call__(self, cls: type[BaseTask]) -> type[BaseTask]:
        instance = cls()

        def task_wrapper(*args, **kwargs):
            return instance.run(*args, **kwargs)

        task_wrapper.__name__ = cls.get_name()
        self._broker.register_task(func=task_wrapper, task_name=cls.get_name())

        return cls
