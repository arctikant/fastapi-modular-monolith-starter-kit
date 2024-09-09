import binascii
import os
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.auth.config import auth_config
from app.auth.schemas.token import AccessToken, PasswordResetToken

pwd_context = CryptContext(schemes=['argon2', 'bcrypt'], deprecated='auto')


def generate_hash(data: str | None) -> str:
    return pwd_context.hash(data)


def verify_hash(data: str, hashed_data: str | None) -> bool:
    return pwd_context.verify(data, hashed_data)


def generate_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expires = datetime.now(UTC) + expires_delta
    else:
        expires = datetime.now(UTC) + timedelta(minutes=30)
    to_encode.update({'exp': expires})

    return jwt.encode(payload=to_encode, key=auth_config.JWT_SECRET_KEY, algorithm=auth_config.JWT_ALGORITHM)


def decode_access_token(token: str) -> AccessToken:
    # Used separate JWT_SECRET_KEY for auth purpose. By changing the JWT_SECRET_KEY you can invalidate
    # all issued token without impact on whole system
    payload = jwt.decode(
        jwt=token,
        key=auth_config.JWT_SECRET_KEY,
        algorithms=[auth_config.JWT_ALGORITHM],
        options={'require': ['exp']},
    )

    return AccessToken(**payload)


def generate_refresh_token(length: int = 24) -> str:
    return binascii.hexlify(os.urandom(length)).decode('utf-8')


def generate_password_reset_token(email: str) -> str:
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=auth_config.EMAIL_RESET_TOKEN_EXPIRE_MINUTES)

    return jwt.encode(
        payload={'exp': expires, 'sub': email},
        key=auth_config.JWT_SECRET_KEY,
        algorithm=auth_config.JWT_ALGORITHM,
    )


def decode_password_reset_token(token: str) -> PasswordResetToken:
    payload = jwt.decode(
        jwt=token,
        key=auth_config.JWT_SECRET_KEY,
        algorithms=[auth_config.JWT_ALGORITHM],
        options={'require': ['exp']},
    )

    return PasswordResetToken(**payload)
