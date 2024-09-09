from typing import Any

from taskiq import AsyncBroker, AsyncTaskiqTask, TaskiqResult

from app.core.services.queue.base_service import (
    QueueResult,
    QueueResultStatus,
    QueueServiceInterface,
)
from app.core.services.queue.base_task import BaseTask


class TaskiqQueueService(QueueServiceInterface):
    def __init__(self, broker: AsyncBroker) -> None:
        self._broker = broker

    async def push(self, task: type[BaseTask], data: dict[str, Any]) -> Any:
        task_instance = await self._broker.find_task(task.get_name()).kiq(**data)  # type: ignore[union-attr]

        return task_instance.task_id

    async def is_ready(self, task_id: str) -> bool:
        return await self._broker.result_backend.is_result_ready(task_id)

    async def get_result(self, task_id: str) -> QueueResult:
        result = await self._broker.result_backend.get_result(task_id)

        return self.__class__._convert_result(result)

    async def wait_result(
        self, task_id: str, check_interval: float | None = None, timeout: float | None = None
    ) -> QueueResult:
        task_instance = AsyncTaskiqTask(
            task_id=task_id,
            result_backend=self._broker.result_backend,
        )
        result = await task_instance.wait_result(check_interval=check_interval or 0.2, timeout=timeout or -1.0)

        return self.__class__._convert_result(result)

    @staticmethod
    def _convert_result(result: TaskiqResult) -> QueueResult:
        return QueueResult(
            status=QueueResultStatus.ERROR if result.is_err else QueueResultStatus.SUCCESS,
            response=result.return_value,
        )
