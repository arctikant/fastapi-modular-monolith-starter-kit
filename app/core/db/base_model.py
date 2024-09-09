from datetime import UTC, datetime
from typing import Any, Self

from sqlalchemy import DateTime, select
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from sqlalchemy.sql import func


class BaseModel(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict[str, Any]:
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(**{k: v for k, v in data.items() if k in cls._get_field_names()})

    def update(self, data: dict[str, Any]) -> None:
        for key, value in data.items():
            if key in self._get_field_names():
                setattr(self, key, value)

    @classmethod
    def _get_field_names(cls) -> list[str]:
        return [column.name for column in cls.__table__.columns]


class SoftDeleteMixin:
    @declared_attr
    def deleted_at(cls) -> Mapped[datetime | None]:
        return mapped_column(DateTime, nullable=True)

    @classmethod
    def select_not_deleted(cls):
        return select(cls).where(cls.deleted_at.is_(None))

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)

    def is_deleted(self) -> bool:
        return self.deleted_at is not None
