from datetime import UTC, datetime, timedelta

import factory

from app.auth.models.refresh_token import RefreshToken
from app.auth.security import generate_hash, generate_refresh_token
from tests.factories.async_alchemy_factory import AsyncSQLAlchemyModelFactory


class RefreshTokenFactory(AsyncSQLAlchemyModelFactory):
    class Meta:
        model = RefreshToken

    token = factory.LazyFunction(lambda: generate_refresh_token(12))
    hash = factory.LazyAttribute(lambda obj: generate_hash(obj.token))
    expires_at = datetime.now(UTC) + timedelta(days=1)
