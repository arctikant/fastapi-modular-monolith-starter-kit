from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from faker import Faker
from freezegun import freeze_time
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import security
from app.auth.config import auth_config
from app.auth.emails.templates import PasswordReset, UserRegistration
from app.auth.events import UserCreated
from app.auth.exceptions import ActionNotAllowed, InvalidInput
from app.auth.models.user import User, UserStatus
from app.auth.schemas.token import RefreshTokenBase, TokenGroup
from app.auth.schemas.user import UserCreate
from app.auth.services.auth import AuthService
from app.core.services.mail import EmailData
from tests.factories.user import UserFactory


class TestAuthService:
    # Fixtures

    @pytest.fixture
    def mock_mail_service(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_event_service(self) -> Mock:
        return Mock()

    @pytest.fixture
    def auth_service(self, db: AsyncSession, mock_mail_service: AsyncMock, mock_event_service: Mock) -> AuthService:
        return AuthService(db=db, mail=mock_mail_service, events=mock_event_service)

    @pytest.fixture(autouse=True)
    def init_factories(self, db: AsyncSession) -> None:
        UserFactory._meta.sqlalchemy_session = db

    # Tests

    async def test_generate_token(self, auth_service: AuthService, db: AsyncSession) -> None:
        user = await UserFactory.create()

        token = await auth_service.generate_token(user.email, UserFactory.get_password())
        self._check_token_group(token=token, user=user)

        # Check negative cases
        with pytest.raises(InvalidInput, match='Invalid email or password'):
            await auth_service.generate_token(user.email, '1111111111')

        await db.execute(update(User).where(User.id == user.id).values(status_id=UserStatus.INACTIVE.value))
        await db.commit()

        with pytest.raises(InvalidInput, match='Invalid email or password'):
            await auth_service.generate_token(user.email, UserFactory.get_password())

    async def test_refresh_token(self, auth_service: AuthService, db: AsyncSession) -> None:
        user = await UserFactory.create()
        initial = await auth_service.generate_token(user.email, UserFactory.get_password())
        refreshed = await auth_service.refresh_token(initial.refresh_token.token)

        # Check that refreshed token is valid
        self._check_token_group(token=refreshed, user=user)

        # Check first refresh token is not active anymore
        with pytest.raises(InvalidInput, match='Invalid refresh token'):
            await auth_service.refresh_token(initial.refresh_token.token)

        # Check that refresh token can expire
        exp = datetime.now(UTC) + timedelta(days=auth_config.REFRESH_TOKEN_EXPIRE_DAYS) + timedelta(minutes=1)
        with freeze_time(exp):
            with pytest.raises(InvalidInput, match='Invalid refresh token'):
                await auth_service.refresh_token(refreshed.refresh_token.token)

        await db.execute(update(User).where(User.id == user.id).values(status_id=UserStatus.INACTIVE.value))
        await db.commit()

        # Check that inactive user can't refresh token
        with pytest.raises(InvalidInput, match='Invalid refresh token'):
            await auth_service.refresh_token(refreshed.refresh_token.token)

    async def test_register(
        self,
        auth_service: AuthService,
        db: AsyncSession,
        faker: Faker,
        mock_mail_service: AsyncMock,
        mock_event_service: Mock,
    ) -> None:
        user_data = UserCreate(
            username=faker.name(),
            email=faker.email(),
            password=faker.password(),
        )

        await auth_service.register(user_data)

        # Check email sending
        mock_mail_service.queue.assert_called_once()
        template_arg = mock_mail_service.queue.call_args.kwargs['template']
        email_data_arg = mock_mail_service.queue.call_args.kwargs['email_data']

        assert isinstance(template_arg, UserRegistration)
        assert isinstance(email_data_arg, EmailData)
        assert email_data_arg.subject == 'Successful registration'
        assert email_data_arg.recipient == user_data.email

        # Check event dispatching
        mock_event_service.dispatch.assert_called_once()
        event_arg = mock_event_service.dispatch.call_args[0][0]

        assert isinstance(event_arg, UserCreated)
        assert event_arg.email == user_data.email
        assert event_arg.username == user_data.username

        result = await db.execute(select(User).where(User.email == user_data.email))  # type: ignore
        registered = result.scalars().first()

        assert registered
        assert registered.username == user_data.username

        # Check negative cases
        with patch('app.auth.config.auth_config.USER_REGISTRATION_ALLOWED', False):
            with pytest.raises(ActionNotAllowed, match='User registration is not allowed on this server'):
                await auth_service.register(user_data)

        with pytest.raises(InvalidInput, match="Can't register user with this credentials"):
            await auth_service.register(user_data)

    async def test_reset_password(
        self, auth_service: AuthService, db: AsyncSession, mock_mail_service: AsyncMock
    ) -> None:
        user = await UserFactory.create()

        # Check restore_password action
        await auth_service.restore_password(user.email)

        # Check email sending
        mock_mail_service.queue.assert_called_once()
        template_arg = mock_mail_service.queue.call_args.kwargs['template']
        email_data_arg = mock_mail_service.queue.call_args.kwargs['email_data']

        assert isinstance(template_arg, PasswordReset)
        assert isinstance(email_data_arg, EmailData)
        assert email_data_arg.subject == 'Password restore'
        assert email_data_arg.recipient == user.email

        # Check token payload
        reset_token = security.decode_password_reset_token(template_arg.token)
        assert reset_token.sub == user.email

        # Check negative cases
        await db.execute(update(User).where(User.id == user.id).values(status_id=UserStatus.INACTIVE.value))
        await db.commit()

        with pytest.raises(InvalidInput, match="Can't restore account with this email"):
            await auth_service.restore_password(user.email)

        await db.execute(update(User).where(User.id == user.id).values(status_id=UserStatus.ACTIVE.value))
        await auth_service._user_repository.delete(db=db, model_id=user.id)
        await db.commit()

        with pytest.raises(InvalidInput, match="Can't restore account with this email"):
            await auth_service.restore_password(user.email)

        # Test reset_password action
        await db.execute(update(User).where(User.id == user.id).values(deleted_at=None))
        await db.commit()

        await auth_service.reset_password(template_arg.token, '11111111')

        result = await db.execute(select(User).where(User.email == user.email))  # type: ignore
        updated = result.scalars().first()

        assert updated
        assert security.verify_hash(data='11111111', hashed_data=updated.password_hash)  # type: ignore[arg-type]

        # Check negative cases
        with pytest.raises(InvalidInput, match='Invalid password reset token'):
            await auth_service.reset_password('wrong_reset_token', '11111111')

        # Check that reset token can expiration
        with freeze_time(datetime.now(UTC) + timedelta(minutes=auth_config.EMAIL_RESET_TOKEN_EXPIRE_MINUTES + 1)):
            with pytest.raises(InvalidInput, match='Invalid password reset token'):
                await auth_service.reset_password(template_arg.token, '11111111')

        await db.execute(update(User).where(User.id == user.id).values(status_id=UserStatus.INACTIVE.value))
        await db.commit()

        with pytest.raises(InvalidInput, match='Invalid password reset token'):
            await auth_service.reset_password(template_arg.token, '11111111')

    async def test_get_user_by_token(self, auth_service: AuthService, db: AsyncSession) -> None:
        user = await UserFactory.create()
        token_group = await auth_service.generate_token(user.email, UserFactory.get_password())
        retrieved = await auth_service.get_user_by_access_token(token_group.access_token)

        assert retrieved
        assert isinstance(retrieved, User)
        assert retrieved.id == user.id

        # Check negative cases
        with pytest.raises(InvalidInput, match='Invalid access token'):
            await auth_service.get_user_by_access_token('wrong_access_token')

        # Check that access token can expire
        with freeze_time(datetime.now(UTC) + timedelta(minutes=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES + 1)):
            with pytest.raises(InvalidInput, match='Invalid access token'):
                await auth_service.get_user_by_access_token(token_group.access_token)

        await auth_service._user_repository.delete(db=db, model_id=user.id)
        await auth_service._user_repository.commit(db)

        with pytest.raises(InvalidInput, match='Invalid access token'):
            await auth_service.get_user_by_access_token(token_group.access_token)

    def _check_token_group(self, token: TokenGroup, user: User) -> None:
        assert token
        assert token.access_token and isinstance(token.access_token, str)
        assert isinstance(token, TokenGroup)
        assert isinstance(token.refresh_token, RefreshTokenBase)

        # Check access token
        access_token = security.decode_access_token(token.access_token)
        assert access_token.sub == user.id

        # Check refresh token
        assert isinstance(token.refresh_token.token, str) and len(token.refresh_token.token) == 48
        assert token.refresh_token.user_id == user.id
