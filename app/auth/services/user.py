from typing import TypeVar

from pydantic import BaseModel as BaseSchema

from app.auth.events import UserDeleted
from app.auth.exceptions import InvalidInput
from app.auth.models.user import User
from app.auth.repositories.refresh_token import RefreshTokenRepository
from app.auth.repositories.user import UserRepository
from app.auth.schemas.user import UserUpdate
from app.core.db import ListParams, PaginatedResult
from app.core.services.events import EventsServiceInterface

T = TypeVar('T', bound=BaseSchema)


class UserService:
    def __init__(
            self,
            user_repo: UserRepository,
            refresh_token_repo: RefreshTokenRepository,
            events: EventsServiceInterface,
    ) -> None:
        self._events = events
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo

    async def get_list(self, params: ListParams, schema: type[T] | None = None) -> PaginatedResult[T]:
        return await self._user_repo.get_list(params=params, schema=schema)

    async def get(self, user_id: int) -> User | None:
        return await self._user_repo.get(user_id)

    async def update(self, user: User, user_data: UserUpdate) -> User:
        if user_data.email:
            existing_user = await self._user_repo.get_by_email(user_data.email)
            if existing_user and existing_user.id != user.id:
                raise InvalidInput("Can't update user with provided data")

        result = await self._user_repo.update(model=user, data=user_data)
        await self._user_repo.commit()

        return result

    async def delete(self, user_id: int | None = None, user: User | None = None) -> None:
        user_id = user.id if user else user_id
        if user_id is None:
            raise InvalidInput('Either user_id or user must be provided')

        await self._refresh_token_repo.delete_by_user_id(user_id=user_id)
        await self._user_repo.delete(model_id=user_id, model=user)
        await self._user_repo.commit()

        self._events.dispatch(UserDeleted(id=user_id))
