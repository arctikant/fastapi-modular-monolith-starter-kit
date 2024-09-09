from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.security import verify_hash
from app.core.db import BaseModel


class RefreshToken(BaseModel):
    __tablename__ = 'auth_refresh_tokens'

    token: Mapped[str] = mapped_column(String(24), primary_key=True)
    hash: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(ForeignKey('auth_users.id'), index=True, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    user: Mapped['User'] = relationship(back_populates='refresh_tokens')  # type: ignore # noqa: F821

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at

    def verify(self, token) -> bool:
        return verify_hash(token, self.hash)
