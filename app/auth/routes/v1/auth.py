from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.deps import AuthService
from app.auth.exceptions import InvalidInput
from app.auth.schemas.token import RefreshTokenRequest, TokenGroupResponse
from app.auth.schemas.user import (
    PasswordResetRequest,
    PasswordRestoreRequest,
    UserCreate,
    UserCreateRequest,
    UserResponse,
)
from app.core.api import ConfigurableRateLimiter, Response

router = APIRouter(dependencies=[Depends(ConfigurableRateLimiter(times=3, seconds=60))])


@router.post('/login')
async def login(
    auth_service: AuthService, request: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Response[TokenGroupResponse]:
    try:
        token_group = await auth_service.generate_token(email=request.username, password=request.password)
    except InvalidInput as e:
        raise HTTPException(status_code=e.status_code, detail=e.message, headers={'WWW-Authenticate': 'Bearer'})

    return Response(data=TokenGroupResponse(**token_group.model_dump(exclude_unset=True), token_type='bearer'))


@router.post('/refresh-token')
async def refresh_token(request: RefreshTokenRequest, auth_service: AuthService) -> Response[TokenGroupResponse]:
    try:
        token_group = await auth_service.refresh_token(refresh_token=request.refresh_token)
    except InvalidInput as e:
        raise HTTPException(status_code=e.status_code, detail=e.message, headers={'WWW-Authenticate': 'Bearer'})

    return Response(data=TokenGroupResponse(**token_group.model_dump(exclude_unset=True), token_type='bearer'))


@router.post('/register')
async def register(request: UserCreateRequest, auth_service: AuthService) -> Response[UserResponse]:
    user = await auth_service.register(UserCreate(**request.model_dump(exclude_none=True, exclude_unset=True)))

    return Response(data=user)


@router.post('/restore-password')
async def restore_password(request: PasswordRestoreRequest, auth_service: AuthService) -> Response:
    await auth_service.restore_password(request.email)

    return Response(message='Password recovery email successfully sent')


@router.post('/reset-password')
async def reset_password(request: PasswordResetRequest, auth_service: AuthService) -> Response:
    await auth_service.reset_password(request.token, request.password)

    return Response(message='Password successfully reset')
