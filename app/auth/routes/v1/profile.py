from fastapi import APIRouter, Depends

from app.auth.dependencies.services import ActiveUserDep, UserServiceDep
from app.auth.schemas.user import UserResponse, UserUpdate, UserUpdateRequest
from app.core.api import ConfigurableRateLimiter, Response

router = APIRouter(dependencies=[Depends(ConfigurableRateLimiter(times=3, seconds=60))])


@router.get('')
async def get(user: ActiveUserDep) -> Response[UserResponse]:
    return Response(data=user)


@router.patch('')
async def update(
    request: UserUpdateRequest, user: ActiveUserDep, user_service: UserServiceDep
) -> Response[UserResponse]:
    user = await user_service.update(
        user=user, user_data=UserUpdate(**request.model_dump(exclude_none=True, exclude_unset=True))
    )

    return Response(data=user)


@router.delete('')
async def delete(user: ActiveUserDep, user_service: UserServiceDep) -> Response:
    await user_service.delete(user=user)

    return Response(message='User was successfully deleted')
