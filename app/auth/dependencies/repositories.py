from typing import Annotated

from fastapi import Depends

from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import User
from app.auth.repositories.refresh_token import RefreshTokenRepository
from app.auth.repositories.user import UserRepository
from app.core.deps import DBSessionDep


def get_user_repository(db: DBSessionDep) -> UserRepository:
    return UserRepository(db=db, model=User)

def get_refresh_token_repository(db: DBSessionDep) -> RefreshTokenRepository:
    return RefreshTokenRepository(db=db, model=RefreshToken)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
RefreshTokenRepoDep = Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)]
