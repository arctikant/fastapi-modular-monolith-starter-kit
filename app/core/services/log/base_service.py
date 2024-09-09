from abc import ABC, abstractmethod
from typing import Any


class LogServiceInterface(ABC):
    @abstractmethod
    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def info(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def error(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def a_debug(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def a_info(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def a_warning(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def a_error(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def a_critical(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def a_exception(self, msg: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
