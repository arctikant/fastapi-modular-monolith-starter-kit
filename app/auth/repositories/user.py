from app.auth.models.user import User
from app.auth.schemas.user import UserCreate, UserUpdate
from app.auth.security import generate_hash, verify_hash
from app.core.db import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    async def get_by_email(self, email: str) -> User:
        result = await self._db.execute(User.select_not_deleted().where(User.email == email))
        return result.scalars().first()

    async def create(self, data: UserCreate) -> User:
        modified = data.model_copy()

        modified.password_hash = generate_hash(data.password)
        modified.password = None

        return await super().create(modified)

    async def update(self, model: User, data: UserUpdate) -> User:
        modified = data.model_copy()

        if modified.password:
            modified.password_hash = generate_hash(modified.password)
            modified.password = None

        return await super().update(model=model, data=modified)

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.get_by_email(email)
        if not user:
            return None

        if not verify_hash(data=password, hashed_data=user.password_hash):
            return None

        return user
