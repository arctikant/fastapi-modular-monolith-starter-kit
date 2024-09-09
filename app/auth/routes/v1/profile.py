from fastapi import APIRouter, Depends

from app.auth.deps import ActiveUserModel, UserService
from app.auth.schemas.user import UserResponse, UserUpdate, UserUpdateRequest
from app.core.api import ConfigurableRateLimiter, Response

router = APIRouter(dependencies=[Depends(ConfigurableRateLimiter(times=3, seconds=60))])


@router.get('')
async def get(user: ActiveUserModel) -> Response[UserResponse]:
    return Response(data=user)


@router.patch('')
async def update(
    request: UserUpdateRequest, user: ActiveUserModel, user_service: UserService
) -> Response[UserResponse]:
    user = await user_service.update(
        user=user, user_data=UserUpdate(**request.model_dump(exclude_none=True, exclude_unset=True))
    )

    return Response(data=user)


@router.delete('')
async def delete(user: ActiveUserModel, user_service: UserService) -> Response:
    await user_service.delete(user=user)

    return Response(message='User was successfully deleted')
