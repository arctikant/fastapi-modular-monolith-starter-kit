from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.auth.dependencies.repositories import RefreshTokenRepoDep, UserRepoDep
from app.auth.exceptions import InvalidInput
from app.auth.gateway import AuthGateway as AuthGatewayClass
from app.auth.gateway import AuthGatewayInterface
from app.auth.models.user import User
from app.auth.schemas.user import UserDTO
from app.auth.services.auth import AuthService as AuthServiceClass
from app.auth.services.user import UserService as UserServiceClass
from app.core.configs import app_config
from app.core.deps import EventsServiceDep, MailServiceDep

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f'{app_config.API_V1_STR}/auth/access-token')


async def get_auth_service(
        user_repo: UserRepoDep,
        refresh_token_repo: RefreshTokenRepoDep,
        mail: MailServiceDep,
        events: EventsServiceDep,
) -> AuthServiceClass:
    return AuthServiceClass(user_repo=user_repo, refresh_token_repo=refresh_token_repo, mail=mail, events=events)


async def get_user_service(
        user_repo: UserRepoDep,
        refresh_token_repo: RefreshTokenRepoDep,
        events: EventsServiceDep,
) -> UserServiceClass:
    return UserServiceClass(user_repo=user_repo, refresh_token_repo=refresh_token_repo, events=events)


async def get_gateway(user_service: Annotated[UserServiceClass, Depends(get_user_service)]) -> AuthGatewayInterface:
    return AuthGatewayClass(user_service=user_service)


class CurrentUserGetter:
    def __init__(self, schema: type[BaseModel] | None = None):
        self._schema = schema

    async def __call__(
        self,
        auth_service: Annotated[AuthServiceClass, Depends(get_auth_service)],
        token: Annotated[str, Depends(reusable_oauth2)],
    ) -> User | BaseModel:
        try:
            user = await auth_service.get_user_by_access_token(token)
        except InvalidInput:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid credentials',
                headers={'WWW-Authenticate': 'Bearer'},
            )

        return self._schema(**user.to_dict()) if self._schema else user


class ActiveUserGetter:
    def __init__(self, schema: type[BaseModel] | None = None):
        self._schema = schema

    async def __call__(self, user: Annotated[User, Depends(CurrentUserGetter())]) -> User | BaseModel:
        if not user.is_active():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalidate credentials',
                headers={'WWW-Authenticate': 'Bearer'},
            )

        return self._schema(**user.to_dict()) if self._schema else user


AuthServiceDep = Annotated[AuthServiceClass, Depends(get_auth_service)]
UserServiceDep = Annotated[UserServiceClass, Depends(get_user_service)]
CurrentUserDep = Annotated[User, Depends(CurrentUserGetter())]
ActiveUserDep = Annotated[User, Depends(ActiveUserGetter())]

# External

CurrentUser = Annotated[User, Depends(CurrentUserGetter(UserDTO))]
ActiveUser = Annotated[User, Depends(ActiveUserGetter(UserDTO))]
AuthGateway = Annotated[AuthGatewayInterface, Depends(get_gateway)]
