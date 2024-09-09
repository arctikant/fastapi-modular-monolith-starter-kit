from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class BaseTemplate(ABC):
    _env: Environment | None = None

    @property
    def env(self) -> Environment:
        if self.__class__._env is None:
            self.__class__._env = Environment(
                loader=FileSystemLoader(self._get_dir()), autoescape=select_autoescape(['html'])
            )
        return self.__class__._env

    @abstractmethod
    def _get_dir(self) -> Path:
        raise NotImplementedError

    @abstractmethod
    def _get_name(self) -> str:
        raise NotImplementedError

    def _get_data(self) -> dict[str, Any]:
        # Remove protected and private attributes
        return {k: v for k, v in vars(self).items() if not k.startswith('_') and not k.startswith('__')}

    def render(self) -> str:
        try:
            return self.env.get_template(self._get_name()).render(self._get_data())
        except Exception as e:
            raise RuntimeError(f"Failed to render mail template '{self._get_name()}': {str(e)}")
