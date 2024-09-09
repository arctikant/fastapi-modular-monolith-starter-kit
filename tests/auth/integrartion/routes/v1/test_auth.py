from datetime import datetime

import pytest
from cerberus import Validator
from fastapi import status as http_status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from app.auth.models.user import User
from app.auth.security import generate_password_reset_token, verify_hash
from app.core.api import ResponseStatus
from app.core.configs import app_config
from tests.factories.user import UserFactory


class TestAuthRouter:
    # Fixtures

    @pytest.fixture(autouse=True)
    def init_factories(self, db: AsyncSession) -> None:
        UserFactory._meta.sqlalchemy_session = db

    # Tests

    async def test_user_can_login(self, client: AsyncClient) -> None:
        user = await UserFactory.create()
        response = await client.post(
            f'{app_config.API_V1_STR}/auth/login',
            data={
                'username': user.email,
                'password': UserFactory.get_password(),
            },
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
                    'access_token': {'type': 'string'},
                    'refresh_token': {
                        'type': 'dict',
                        'schema': {
                            'token': {'type': 'string'},
                            'expires_at': {
                                'type': 'string',
                                'check_with': lambda f, s, e: datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ'),
                            },
                        },
                    },
                    'token_type': {'type': 'string'},
                },
            },
        }

        assert Validator(schema).validate(body)

    async def test_user_cant_login_with_wrong_password(self, client: AsyncClient) -> None:
        user = await UserFactory.create()
        response = await client.post(
            f'{app_config.API_V1_STR}/auth/login',
            data={
                'username': user.email,
                'password': 'wrong_password',
            },
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert body['code'] == ResponseStatus.ERROR.value

    async def test_user_can_refresh_token(self, client: AsyncClient) -> None:
        user = await UserFactory.create()
        login_response = await client.post(
            f'{app_config.API_V1_STR}/auth/login',
            data={
                'username': user.email,
                'password': UserFactory.get_password(),
            },
        )

        response = await client.post(
            f'{app_config.API_V1_STR}/auth/refresh-token',
            json={'refresh_token': login_response.json()['data']['refresh_token']['token']},
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
                    'access_token': {'type': 'string'},
                    'refresh_token': {
                        'type': 'dict',
                        'schema': {
                            'token': {'type': 'string'},
                            'expires_at': {
                                'type': 'string',
                                'check_with': lambda f, s, e: datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ'),
                            },
                        },
                    },
                    'token_type': {'type': 'string'},
                },
            },
        }

        assert Validator(schema).validate(body)

    async def test_user_cant_refresh_token_with_wrong_token(self, client: AsyncClient) -> None:
        user = await UserFactory.create()
        await client.post(
            f'{app_config.API_V1_STR}/auth/login',
            data={
                'username': user.email,
                'password': UserFactory.get_password(),
            },
        )

        response = await client.post(
            f'{app_config.API_V1_STR}/auth/refresh-token',
            json={
                'refresh_token': 'wrong_refresh_token',
            },
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert body['code'] == ResponseStatus.ERROR.value

    async def test_user_can_register(self, client: AsyncClient, db: AsyncSession) -> None:
        response = await client.post(
            f'{app_config.API_V1_STR}/auth/register',
            json={
                'username': 'username',
                'email': 'username@test.com',
                'password': '11111111',
            },
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
                    'email': {'type': 'string', 'regex': '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'},
                    'status_id': {'type': 'integer'},
                },
            },
        }

        assert Validator(schema).validate(body)

        result = await db.execute(select(count()).select_from(User).where(User.email == 'username@test.com'))  # type: ignore
        assert result.scalar_one() == 1

    async def test_user_cant_register_with_short_password(self, client: AsyncClient) -> None:
        response = await client.post(
            f'{app_config.API_V1_STR}/auth/register',
            json={
                'username': 'username',
                'email': 'username@test.com',
                'password': '1111111',
            },
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        assert body['code'] == ResponseStatus.VALIDATION_ERROR.value

    async def test_user_can_reset_password(self, client: AsyncClient, db: AsyncSession) -> None:
        user = await UserFactory.create()

        response = await client.post(
            f'{app_config.API_V1_STR}/auth/restore-password',
            json={
                'email': user.email,
            },
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_200_OK
        assert body['code'] == ResponseStatus.SUCCESS.value

        token = generate_password_reset_token(user.email)
        new_password = '11111111'
        response = await client.post(
            f'{app_config.API_V1_STR}/auth/reset-password',
            json={
                'token': token,
                'password': new_password,
            },
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_200_OK
        assert body['code'] == ResponseStatus.SUCCESS.value

        await db.refresh(user)

        assert user
        assert verify_hash(data=new_password, hashed_data=user.password_hash)  # type: ignore[arg-type]

    async def test_user_cant_restore_password_for_non_existent_account(self, client: AsyncClient) -> None:
        response = await client.post(
            f'{app_config.API_V1_STR}/auth/restore-password',
            json={
                'email': 'non-existing@example.com',
            },
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert body['code'] == ResponseStatus.INVALID_INPUT.value

    async def test_user_cant_reset_password_with_wrong_token(self, client: AsyncClient) -> None:
        response = await client.post(
            f'{app_config.API_V1_STR}/auth/reset-password',
            json={
                'token': 'wrong_token',
                'password': 'new_password',
            },
        )
        body = response.json()

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert body['code'] == ResponseStatus.INVALID_INPUT.value
