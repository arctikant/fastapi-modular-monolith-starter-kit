import pytest
from cerberus import Validator
from fastapi import status as http_status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api import ResponseStatus
from app.core.configs import app_config
from tests.factories.user import UserFactory
from tests.utils import login_user


class TestProfileRouter:
    # Fixtures

    @pytest.fixture(autouse=True)
    def init_factories(self, db: AsyncSession) -> None:
        UserFactory._meta.sqlalchemy_session = db

    # Tests

    async def test_user_can_get_its_profile(self, client: AsyncClient):
        user = await UserFactory.create()
        tokens = await login_user(client=client, user=user)

        response = await client.get(
            f'{app_config.API_V1_STR}/profile',
            headers={'Authorization': f'Bearer {tokens['access_token']}'},
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_200_OK
        assert body['code'] == ResponseStatus.SUCCESS.value
        assert self._validate_profile_response_structure(body)

    async def test_unauthorized_user_cant_get_profile(self, client: AsyncClient):
        response = await client.get(
            f'{app_config.API_V1_STR}/profile',
            headers={'Authorization': 'Bearer wrong_token'},
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED
        assert body['code'] == ResponseStatus.NOT_AUTHORIZED.value

    async def test_user_can_update_its_profile(self, client: AsyncClient, db: AsyncSession):
        user = await UserFactory.create()
        tokens = await login_user(client=client, user=user)

        response = await client.patch(
            f'{app_config.API_V1_STR}/profile',
            headers={'Authorization': f'Bearer {tokens['access_token']}'},
            json={'username': 'new_username'},
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_200_OK
        assert body['code'] == ResponseStatus.SUCCESS.value
        assert body['data']['username'] == 'new_username'
        assert self._validate_profile_response_structure(body)

        await db.refresh(user)
        assert user.username == 'new_username'

    async def test_unauthorized_user_cant_update_profile(self, client: AsyncClient):
        response = await client.patch(
            f'{app_config.API_V1_STR}/profile',
            headers={'Authorization': 'Bearer wrong_token'},
            json={'username': 'new_username'},
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED
        assert body['code'] == ResponseStatus.NOT_AUTHORIZED.value

    async def test_user_can_delete_its_profile(self, client: AsyncClient, db: AsyncSession):
        user = await UserFactory.create()
        tokens = await login_user(client=client, user=user)

        response = await client.delete(
            f'{app_config.API_V1_STR}/profile',
            headers={'Authorization': f'Bearer {tokens['access_token']}'},
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_200_OK
        assert body['code'] == ResponseStatus.SUCCESS.value

        await db.refresh(user)
        assert user and user.deleted_at is not None

    async def test_unauthorized_user_cant_delete_profile(self, client: AsyncClient):
        response = await client.delete(
            f'{app_config.API_V1_STR}/profile',
            headers={'Authorization': 'Bearer wrong_token'},
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED
        assert body['code'] == ResponseStatus.NOT_AUTHORIZED.value

    def _validate_profile_response_structure(self, body: dict) -> bool:
        schema = {
            'code': {'type': 'integer'},
            'message': {'type': 'string'},
            'data': {
                'type': 'dict',
                'schema': {
                    'id': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'email': {'type': 'string'},
                    'status_id': {'type': 'integer'},
                },
            },
        }

        return Validator(schema).validate(body)
