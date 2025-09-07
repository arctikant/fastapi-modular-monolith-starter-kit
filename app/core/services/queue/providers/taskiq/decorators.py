import functools

from taskiq import AsyncBroker

from app.core.services.queue.base_task import BaseTask


class TaskiqQueuedDecorator:
    def __init__(self, broker: AsyncBroker) -> None:
        self._broker = broker

    def __call__(self, cls: type[BaseTask]) -> type[BaseTask]:
        instance = cls()

        async def wrapper(*args, **kwargs):
            return await instance.run(*args, **kwargs)

        functools.update_wrapper(wrapper, instance.run, assigned=("__doc__",), updated=())

        self._broker.register_task(func=wrapper, task_name=cls.get_name())
        return cls
