from typing import TypeVar

from pydantic import BaseModel as BaseSchema
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.events import UserDeleted
from app.auth.exceptions import InvalidInput
from app.auth.models.user import User
from app.auth.repositories.refresh_token import refresh_token_repository
from app.auth.repositories.user import user_repository
from app.auth.schemas.user import UserUpdate
from app.core.db import ListParams, PaginatedResult
from app.core.services.events import EventsServiceInterface

T = TypeVar('T', bound=BaseSchema)


class UserService:
    def __init__(self, db: AsyncSession, events: EventsServiceInterface) -> None:
        self._db = db
        self._events = events
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository

    async def get_list(self, params: ListParams, schema: type[T] | None = None) -> PaginatedResult[T]:
        return await self._user_repository.get_list(db=self._db, params=params, schema=schema)

    async def get(self, user_id: int) -> User | None:
        return await self._user_repository.get(db=self._db, model_id=user_id)

    async def update(self, user: User, user_data: UserUpdate) -> User:
        if user_data.email:
            existing_user = await self._user_repository.get_by_email(self._db, user_data.email)
            if existing_user and existing_user.id != user.id:
                raise InvalidInput("Can't update user with provided data")

        result = await self._user_repository.update(db=self._db, model=user, data=user_data)
        await self._user_repository.commit(db=self._db)

        return result

    async def delete(self, user_id: int | None = None, user: User | None = None) -> None:
        user_id = user.id if user else user_id
        if user_id is None:
            raise InvalidInput('Either user_id or user must be provided')

        await self._refresh_token_repository.delete_by_user_id(db=self._db, user_id=user_id)
        await self._user_repository.delete(db=self._db, model_id=user_id, model=user)
        await self._user_repository.commit(db=self._db)

        self._events.dispatch(UserDeleted(id=user_id))
