from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from app.auth.deps import ActiveUserGetter, UserService
from app.auth.schemas.user import (
    UserFilterParam,
    UserListParams,
    UserResponse,
    UserSortParam,
)
from app.core.api import (
    ConfigurableRateLimiter,
    ListParamsBuilder,
    PaginatedResponse,
    Response,
    ResponseMeta,
)

router = APIRouter(
    dependencies=[
        Depends(ConfigurableRateLimiter(times=3, seconds=60)),
        Depends(ActiveUserGetter()),
    ]
)

list_params_builder = ListParamsBuilder(UserListParams, UserSortParam, UserFilterParam)


@router.get('')
async def get_list(
    user_service: UserService, request: UserListParams = Depends(list_params_builder)
) -> PaginatedResponse[list[UserResponse]]:
    users = await user_service.get_list(request, UserResponse)

    return PaginatedResponse(data=users.items, meta=ResponseMeta(pagination=users.pagination))


@router.get('/{user_id}')
async def get(user_id: int, user_service: UserService) -> Response[UserResponse]:
    user = await user_service.get(user_id)

    if user is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail='User not found')

    return Response(data=user)
