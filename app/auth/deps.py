from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.auth.exceptions import InvalidInput
from app.auth.gateway import AuthGateway as AuthGatewayClass
from app.auth.gateway import AuthGatewayInterface
from app.auth.models.user import User
from app.auth.schemas.user import UserDTO
from app.auth.services.auth import AuthService as AuthServiceClass
from app.auth.services.user import UserService as UserServiceClass
from app.core.configs import app_config
from app.core.deps import DBSession, EventsService, MailService

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f'{app_config.API_V1_STR}/auth/access-token')


async def get_auth_service(db: DBSession, mail: MailService, events: EventsService) -> AuthServiceClass:
    return AuthServiceClass(db=db, mail=mail, events=events)


async def get_user_service(db: DBSession, events: EventsService) -> UserServiceClass:
    return UserServiceClass(db=db, events=events)


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


AuthService = Annotated[AuthServiceClass, Depends(get_auth_service)]
UserService = Annotated[UserServiceClass, Depends(get_user_service)]
CurrentUserModel = Annotated[User, Depends(CurrentUserGetter())]
ActiveUserModel = Annotated[User, Depends(ActiveUserGetter())]

# External

CurrentUser = Annotated[User, Depends(CurrentUserGetter(UserDTO))]
ActiveUser = Annotated[User, Depends(ActiveUserGetter(UserDTO))]
AuthGateway = Annotated[AuthGatewayInterface, Depends(get_gateway)]
