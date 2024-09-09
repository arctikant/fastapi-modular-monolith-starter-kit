from abc import ABC, abstractmethod

from app.auth.schemas.user import UserDTO
from app.auth.services.user import UserService
from app.core.db import ListParams, PaginatedResult


class AuthGatewayInterface(ABC):
    @abstractmethod
    async def get_user(self, user_id: int) -> UserDTO | None:
        """
        Returns User model by given user_id.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_user_list(self, params: ListParams) -> PaginatedResult[UserDTO]:
        """
        Returns PaginatedResult with a list of User models. ListParams input parameter can be used
        to pass pagination, sort and filter parameters
        """
        raise NotImplementedError


class AuthGateway(AuthGatewayInterface):
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    async def get_user(self, user_id: int) -> UserDTO | None:
        user = await self._user_service.get(user_id)

        return UserDTO(**user.to_dict()) if user else None

    async def get_user_list(self, params: ListParams) -> PaginatedResult[UserDTO]:
        return await self._user_service.get_list(params, UserDTO)
