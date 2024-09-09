from typing import Any

from app.core.services.log.base_service import LogServiceInterface


class StructLogService(LogServiceInterface):
    def __init__(self, logger: Any) -> None:
        self._logger = logger

    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> Any:
        return self._logger.log(level, msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return self._logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return self._logger.exception(msg, *args, **kwargs)

    async def a_debug(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return await self._logger.adebug(msg, *args, **kwargs)

    async def a_info(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return await self._logger.ainfo(msg, *args, **kwargs)

    async def a_warning(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return await self._logger.awarning(msg, *args, **kwargs)

    async def a_error(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return await self._logger.aerror(msg, *args, **kwargs)

    async def a_critical(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return await self._logger.acritical(msg, *args, **kwargs)

    async def a_exception(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        return await self._logger.aexception(msg, *args, **kwargs)
