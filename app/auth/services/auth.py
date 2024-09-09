from datetime import UTC, datetime, timedelta

from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import security
from app.auth.config import auth_config
from app.auth.emails.templates import PasswordReset, UserRegistration
from app.auth.events import UserCreated
from app.auth.exceptions import ActionNotAllowed, InvalidInput
from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import User
from app.auth.repositories.refresh_token import refresh_token_repository
from app.auth.repositories.user import user_repository
from app.auth.schemas.token import RefreshTokenBase, TokenGroup
from app.auth.schemas.user import UserCreate, UserUpdate
from app.core.configs import app_config
from app.core.db import DatabaseException
from app.core.services.events import EventsServiceInterface
from app.core.services.mail import EmailData, MailServiceInterface


class AuthService:
    def __init__(self, db: AsyncSession, mail: MailServiceInterface, events: EventsServiceInterface) -> None:
        self._db = db
        self._mail = mail
        self._events = events
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository

    async def generate_token(self, email: str, password: str) -> TokenGroup:
        user = await self._user_repository.authenticate(db=self._db, email=email, password=password)
        if not user or not user.is_active():
            raise InvalidInput('Invalid email or password')

        access_token = security.generate_access_token(
            data={'sub': user.id},
            expires_delta=timedelta(minutes=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token_data = await self._upsert_refresh_token(user=user)

        return TokenGroup(access_token=access_token, refresh_token=refresh_token_data)

    async def refresh_token(self, refresh_token: str) -> TokenGroup:
        # IMPROVEMENTS:
        # Implement refresh token families to improve security
        # Store refresh_token in cookie with HttpOnly flag if you have your SPA on subdomain for better security
        token = await self._refresh_token_repository.get_with_user(db=self._db, token=refresh_token)
        if (
            not token
            or not token.user
            or not token.user.is_active()
            or token.is_expired()
            or not token.verify(refresh_token)
        ):
            raise InvalidInput('Invalid refresh token')

        access_token = security.generate_access_token(
            data={'sub': token.user.id},
            expires_delta=timedelta(minutes=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token_data = await self._upsert_refresh_token(token=token, user=token.user)

        return TokenGroup(access_token=access_token, refresh_token=refresh_token_data)

    async def register(self, user_data: UserCreate) -> User:
        # Improvement: implement email confirmation logic

        if not auth_config.USER_REGISTRATION_ALLOWED:
            raise ActionNotAllowed('User registration is not allowed on this server')

        user = await self._user_repository.get_by_email(db=self._db, email=user_data.email)
        if user:
            raise InvalidInput("Can't register user with this credentials")

        try:
            user = await self._user_repository.create(db=self._db, data=user_data)
            await self._user_repository.commit(db=self._db)
        except DatabaseException:
            raise InvalidInput("Can't register user with this credentials")

        # Send email
        email_data = EmailData(subject='Successful registration', recipient=user.email)
        template = UserRegistration(username=user.username, project_name=app_config.PROJECT_NAME)
        await self._mail.queue(template=template, email_data=email_data)

        # Dispatch event
        self._events.dispatch(UserCreated(**user.to_dict()))

        return user

    async def restore_password(self, email: str) -> None:
        user = await self._user_repository.get_by_email(self._db, email)

        if not user or not user.is_active():
            raise InvalidInput("Can't restore account with this email")

        token = security.generate_password_reset_token(email=user.email)

        email_data = EmailData(subject='Password restore', recipient=user.email)
        template = PasswordReset(
            username=user.username,
            link=f'{app_config.app_url}/reset-password?token={token}',
            token=token,
            valid_minutes=auth_config.EMAIL_RESET_TOKEN_EXPIRE_MINUTES,
        )
        await self._mail.queue(template=template, email_data=email_data)

    async def reset_password(self, token: str, password: str) -> None:
        try:
            token_data = security.decode_password_reset_token(token=token)
        except InvalidTokenError:
            raise InvalidInput('Invalid password reset token')

        if not token_data.sub:
            raise InvalidInput('Invalid password reset token')

        user = await self._user_repository.get_by_email(db=self._db, email=token_data.sub)

        if not user or not user.is_active():
            raise InvalidInput('Invalid password reset token')

        await self._user_repository.update(db=self._db, model=user, data=UserUpdate(password=password))
        await self._user_repository.commit(db=self._db)

    async def get_user_by_access_token(self, token: str) -> User:
        try:
            token_data = security.decode_access_token(token)
        except InvalidTokenError:
            raise InvalidInput('Invalid access token')

        if token_data.sub is None:
            raise InvalidInput('Invalid access token')

        user = await self._user_repository.get(self._db, token_data.sub)
        if not user:
            raise InvalidInput('Invalid access token')

        return user

    async def _upsert_refresh_token(self, user: User, token: RefreshToken | None = None) -> RefreshTokenBase:
        refresh_token = RefreshTokenBase(
            token=security.generate_refresh_token(),
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(days=auth_config.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        await self._refresh_token_repository.upsert(db=self._db, model=token, data=refresh_token)
        await self._refresh_token_repository.commit(db=self._db)

        return refresh_token
