from typing import Any, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        env_ignore_empty=True,
        extra='ignore',
    )

    @staticmethod
    def _parse_list(v: Any) -> list[str] | str:
        if isinstance(v, str) and not v.startswith('['):
            return [i.strip() for i in v.split(',')]
        elif isinstance(v, list | str):
            return v
        raise ValueError(v)

    def _check_default_secret(self, name: str) -> None:
        if getattr(self, name) == 'changethis':
            raise ValueError(f"The value of {name} is 'changethis', for security reasons, please change it.")

    _default_secrets: list[str] = []

    @model_validator(mode='after')
    def _enforce_non_default_secrets(self) -> Self:
        for name in self._default_secrets:
            self._check_default_secret(name)

        return self
