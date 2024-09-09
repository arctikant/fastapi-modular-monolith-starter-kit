from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.core.services.queue import BaseTask, QueueResult
from app.core.services.queue.base_service import QueueResultStatus
from app.core.services.queue.providers.taskiq.service import TaskiqQueueService


class TestTask(BaseTask):
    __task_name__ = 'test.task'

    def run(self):
        pass


class TestCeleryQueueService:
    # Fixture

    @pytest.fixture
    def mock_queue(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def queue_service(self, mock_queue: AsyncMock) -> TaskiqQueueService:
        return TaskiqQueueService(mock_queue)

    # Tests

    async def test_push(self) -> None:
        mock_queue = Mock()
        queue_service = TaskiqQueueService(mock_queue)

        task_instance = AsyncMock()
        mock_queue.find_task.return_value = task_instance

        await queue_service.push(
            task=TestTask,
            data={'name': 'John', 'age': 18},
        )

        mock_queue.find_task.assert_called_once_with(TestTask.__task_name__)
        task_instance.kiq.assert_called_once_with(name='John', age=18)

    async def test_is_ready(self, mock_queue: AsyncMock, queue_service: TaskiqQueueService) -> None:
        mock_queue.result_backend.is_result_ready = AsyncMock(return_value=True)
        task_id = '1234567890'

        result = await queue_service.is_ready(task_id)

        mock_queue.result_backend.is_result_ready.assert_called_once_with(task_id)

        assert type(result) is bool
        assert result

    @patch('app.core.services.queue.providers.taskiq.service.AsyncTaskiqTask')
    async def test_wait_result(
        self, task_mock: MagicMock, mock_queue: AsyncMock, queue_service: TaskiqQueueService
    ) -> None:
        task_id = '1234567890'
        mock_queue.result_backend = 'backend'
        queue_result = Mock()
        queue_result.is_err = 0
        queue_result.return_value = 'result'

        task_instance = AsyncMock
        task_instance.wait_result = AsyncMock(return_value=queue_result)
        task_mock.return_value = task_instance

        result = await queue_service.wait_result(task_id=task_id, check_interval=1, timeout=2)

        task_mock.assert_called_once_with(task_id=task_id, result_backend='backend')
        task_instance.wait_result.assert_called_once_with(check_interval=1, timeout=2)

        assert isinstance(result, QueueResult)
        assert result.status == QueueResultStatus.SUCCESS
        assert result.response == 'result'

    async def test_result(self, mock_queue: AsyncMock, queue_service: TaskiqQueueService) -> None:
        queue_result = Mock()
        queue_result.is_err = 0
        queue_result.return_value = 'result'
        mock_queue.result_backend.get_result = AsyncMock(return_value=queue_result)
        task_id = '1234567890'

        result = await queue_service.get_result(task_id)

        mock_queue.result_backend.get_result.assert_called_once_with(task_id)

        assert isinstance(result, QueueResult)
        assert result.status == QueueResultStatus.SUCCESS
        assert result.response == 'result'
