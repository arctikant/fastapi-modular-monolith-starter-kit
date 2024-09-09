import pytest
from cerberus import Validator
from fastapi import status as http_status
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models.user import User, UserStatus
from app.core.api import ResponseStatus
from app.core.configs import app_config
from tests.factories.user import UserFactory
from tests.utils import login_user


class TestUsersRouter:
    # Fixtures

    @pytest.fixture(autouse=True)
    def init_factories(self, db: AsyncSession) -> None:
        UserFactory._meta.sqlalchemy_session = db

    # Tests

    async def test_user_can_get_user_by_id(self, client: AsyncClient):
        users = await UserFactory.create_batch(3)
        tokens = await login_user(client=client, user=users[0])

        response = await client.get(
            f'{app_config.API_V1_STR}/users/{users[1].id}',
            headers={'Authorization': f'Bearer {tokens['access_token']}'},
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_200_OK
        assert body['code'] == ResponseStatus.SUCCESS.value

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

    async def test_unauthorized_user_cant_get_user_by_id(self, client: AsyncClient):
        user = await UserFactory.create()

        response = await client.get(
            f'{app_config.API_V1_STR}/users/{user.id}',
            headers={'Authorization': 'Bearer wrong_token'},
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED
        assert body['code'] == ResponseStatus.NOT_AUTHORIZED.value

    async def test_user_can_get_404_user_not_exists(self, client: AsyncClient):
        user = await UserFactory.create()
        tokens = await login_user(client=client, user=user)

        response = await client.get(
            f'{app_config.API_V1_STR}/users/123',
            headers={'Authorization': f'Bearer {tokens['access_token']}'},
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_404_NOT_FOUND
        assert body['code'] == ResponseStatus.NOT_FOUND_ERROR.value

    async def test_user_can_get_list_of_users(self, client: AsyncClient, db: AsyncSession):
        users = await UserFactory.create_batch(5)
        tokens = await login_user(client=client, user=users[0])

        await db.execute(update(User).where(User.id == users[4].id).values(status_id=UserStatus.INACTIVE.value))
        await db.commit()

        response = await client.get(
            f'{app_config.API_V1_STR}/users',
            headers={'Authorization': f'Bearer {tokens['access_token']}'},
            params={
                'page': 2,
                'per_page': 2,
                'filters': 'status_id:1',
                'sort': 'id:desc,username:asc',
            },
        )

        body = response.json()

        assert response.status_code == http_status.HTTP_200_OK
        assert body['code'] == ResponseStatus.SUCCESS.value
        assert len(body['data']) == 2
        assert body['meta']['pagination']['total'] == 4
        assert body['meta']['pagination']['page'] == 2
        assert body['meta']['pagination']['per_page'] == 2

        schema = {
            'code': {'type': 'integer'},
            'message': {'type': 'string'},
            'data': {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'schema': {
                        'id': {'type': 'integer'},
                        'username': {'type': 'string'},
                        'email': {'type': 'string'},
                        'status_id': {'type': 'integer'},
                    },
                },
            },
            'meta': {
                'type': 'dict',
                'schema': {
                    'total': {'type': 'integer'},
                    'page': {'type': 'integer'},
                    'per_page': {'type': 'integer'},
                },
            },
        }

        return Validator(schema).validate(body)

    async def test_unauthorized_user_cant_get_list_of_users(self, client: AsyncClient):
        await UserFactory.create()

        response = await client.get(
            f'{app_config.API_V1_STR}/users',
            headers={'Authorization': 'Bearer wrong_token'},
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED
        assert body['code'] == ResponseStatus.NOT_AUTHORIZED.value
