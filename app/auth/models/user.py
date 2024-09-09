from enum import Enum

from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import BaseModel, SoftDeleteMixin


class UserStatus(Enum):
    ACTIVE: int = 1
    INACTIVE: int = 2


class User(BaseModel, SoftDeleteMixin):
    __tablename__ = 'auth_users'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    email: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(256))
    status_id: Mapped[int] = mapped_column(SmallInteger(), index=True, default=UserStatus.ACTIVE.value)

    refresh_tokens: Mapped[list['RefreshToken']] = relationship(back_populates='user')  # type: ignore # noqa: F821

    def is_active(self) -> bool:
        return self.status_id == UserStatus.ACTIVE.value
