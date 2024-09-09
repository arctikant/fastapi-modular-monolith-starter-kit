import logging
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.services.log.providers.structlog.service import StructLogService


class TestStructLogService:
    # Fixtures

    @pytest.fixture
    def mock_logger(self) -> Mock:
        return Mock()

    @pytest.fixture
    def mock_async_logger(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def log_service(self, mock_logger: Mock) -> StructLogService:
        return StructLogService(mock_logger)

    @pytest.fixture
    def async_log_service(self, mock_async_logger: AsyncMock) -> StructLogService:
        return StructLogService(mock_async_logger)

    # Tests

    def test_log(self, mock_logger: Mock, log_service: StructLogService) -> None:
        log_service.log(logging.INFO, 'msg', 15, abc='abc')
        mock_logger.log.assert_called_once_with(logging.INFO, 'msg', 15, abc='abc')

    def test_debug(self, mock_logger: Mock, log_service: StructLogService) -> None:
        log_service.debug('msg', 15, abc='abc')
        mock_logger.debug.assert_called_once_with('msg', 15, abc='abc')

    def test_info(self, mock_logger: Mock, log_service: StructLogService) -> None:
        log_service.info('msg', 15, abc='abc')
        mock_logger.info.assert_called_once_with('msg', 15, abc='abc')

    def test_warning(self, mock_logger: Mock, log_service: StructLogService) -> None:
        log_service.warning('msg', 15, abc='abc')
        mock_logger.warning.assert_called_once_with('msg', 15, abc='abc')

    def test_error(self, mock_logger: Mock, log_service: StructLogService) -> None:
        log_service.error('msg', 15, abc='abc')
        mock_logger.error.assert_called_once_with('msg', 15, abc='abc')

    def test_critical(self, mock_logger: Mock, log_service: StructLogService) -> None:
        log_service.critical('msg', 15, abc='abc')
        mock_logger.critical.assert_called_once_with('msg', 15, abc='abc')

    def test_exception(self, mock_logger: Mock, log_service: StructLogService) -> None:
        log_service.exception('msg', 15, abc='abc')
        mock_logger.exception.assert_called_once_with('msg', 15, abc='abc')

    async def test_a_debug(self, mock_async_logger: AsyncMock, async_log_service: StructLogService) -> None:
        await async_log_service.a_debug('msg', 15, abc='abc')
        mock_async_logger.adebug.assert_called_once_with('msg', 15, abc='abc')

    async def test_a_info(self, mock_async_logger: AsyncMock, async_log_service: StructLogService) -> None:
        await async_log_service.a_info('msg', 15, abc='abc')
        mock_async_logger.ainfo.assert_called_once_with('msg', 15, abc='abc')

    async def test_a_warning(self, mock_async_logger: AsyncMock, async_log_service: StructLogService) -> None:
        await async_log_service.a_warning('msg', 15, abc='abc')
        mock_async_logger.awarning.assert_called_once_with('msg', 15, abc='abc')

    async def test_a_error(self, mock_async_logger: AsyncMock, async_log_service: StructLogService) -> None:
        await async_log_service.a_error('msg', 15, abc='abc')
        mock_async_logger.aerror.assert_called_once_with('msg', 15, abc='abc')

    async def test_a_critical(self, mock_async_logger: AsyncMock, async_log_service: StructLogService) -> None:
        await async_log_service.a_critical('msg', 15, abc='abc')
        mock_async_logger.acritical.assert_called_once_with('msg', 15, abc='abc')

    async def test_a_exception(self, mock_async_logger: AsyncMock, async_log_service: StructLogService) -> None:
        await async_log_service.a_exception('msg', 15, abc='abc')
        mock_async_logger.aexception.assert_called_once_with('msg', 15, abc='abc')
