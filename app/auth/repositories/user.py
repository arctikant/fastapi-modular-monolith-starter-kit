from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models.user import User
from app.auth.schemas.user import UserCreate, UserUpdate
from app.auth.security import generate_hash, verify_hash
from app.core.db import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, email: str) -> User:
        result = await db.execute(User.select_not_deleted().where(User.email == email))
        return result.scalars().first()

    async def create(self, db: AsyncSession, data: UserCreate) -> User:
        modified = data.model_copy()

        modified.password_hash = generate_hash(data.password)
        modified.password = None

        return await super().create(db=db, data=modified)

    async def update(self, db: AsyncSession, model: User, data: UserUpdate) -> User:
        modified = data.model_copy()

        if modified.password:
            modified.password_hash = generate_hash(modified.password)
            modified.password = None

        return await super().update(db=db, model=model, data=modified)

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> User | None:
        user = await self.get_by_email(db, email)
        if not user:
            return None

        if not verify_hash(data=password, hashed_data=user.password_hash):
            return None

        return user


user_repository = UserRepository(User)
