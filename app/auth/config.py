from app.core.configs import BaseConfig


class AuthConfig(BaseConfig):
    _default_secrets = ['JWT_SECRET_KEY']

    USER_REGISTRATION_ALLOWED: bool = False

    FIRST_USER_EMAIL: str = ''
    FIRST_USER_PASSWORD: str = ''

    EMAIL_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    JWT_SECRET_KEY: str = ''
    JWT_ALGORITHM: str = 'HS256'


auth_config = AuthConfig()
