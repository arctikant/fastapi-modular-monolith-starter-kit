from httpx import AsyncClient

from app.auth.models.user import User
from app.core.configs import app_config
from tests.factories.user import UserFactory


async def login_user(client: AsyncClient, user: User) -> dict:
    response = await client.post(
        f'{app_config.API_V1_STR}/auth/login',
        data={
            'username': user.email,
            'password': UserFactory.get_password(),
        },
    )
    return response.json()['data']
