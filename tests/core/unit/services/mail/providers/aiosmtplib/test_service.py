from email.message import EmailMessage
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.configs import app_config
from app.core.services.mail import BaseTemplate, EmailData
from app.core.services.mail.providers.aiosmtplib.service import AioSmtpLibMailService
from app.core.services.mail.providers.aiosmtplib.setup import smtp_config
from app.core.services.mail.providers.aiosmtplib.tasks import SendEmail


class TestTemplate(BaseTemplate):
    def _get_dir(self) -> Path:
        return Path('app/some_path')

    def _get_name(self) -> str:
        return 'test_template.html'

    def render(self) -> str:
        return 'test_render'


class TestEmailsMailService:
    # Fixtures

    @pytest.fixture
    def mock_queue_service(self) -> AsyncMock:
        return AsyncMock()

    # Tests

    @patch('app.core.services.mail.providers.aiosmtplib.service.aiosmtplib', new_callable=AsyncMock)
    async def test_send(self, mock_aiosmtplib: AsyncMock, mock_queue_service: Mock) -> None:
        mail_service = AioSmtpLibMailService(queue_service=mock_queue_service)
        template = TestTemplate()
        email_data = EmailData(
            subject='test_subject',
            recipient='test_recipient',
        )

        await mail_service.send(template=template, email_data=email_data)

        mock_aiosmtplib.send.assert_called_once()
        args, kwargs = mock_aiosmtplib.send.call_args

        # Check the message contents
        sent_message = args[0]
        assert isinstance(sent_message, EmailMessage)
        assert sent_message['From'] == f'{app_config.EMAIL_SENDER_NAME} <{app_config.EMAIL_SENDER_ADDRESS}>'
        assert sent_message['To'] == email_data.recipient
        assert sent_message['Subject'] == f'{app_config.PROJECT_NAME} | {email_data.subject}'

        # Check the message body
        html_content = None
        for part in sent_message.walk():
            if part.get_content_type() == 'text/html':
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    html_content = payload.decode()
                elif isinstance(payload, str):
                    html_content = payload

        assert html_content == 'test_render\n'

        # Check the SMTP config
        assert kwargs == smtp_config

        # Check custom sender data
        email_data = EmailData(
            subject='test_subject',
            recipient='test_recipient',
            sender_address='test_sender_address',
            sender_name='test_sender_name',
        )

        mock_aiosmtplib.reset_mock()
        await mail_service.send(template=template, email_data=email_data)

        mock_aiosmtplib.send.assert_called_once()
        args, kwargs = mock_aiosmtplib.send.call_args

        assert args[0]['From'] == 'test_sender_name <test_sender_address>'

    async def test_queue(self, mock_queue_service: AsyncMock) -> None:
        mail_service = AioSmtpLibMailService(queue_service=mock_queue_service)

        template = TestTemplate()
        email_data = EmailData(
            subject='test_subject',
            recipient='test_recipient',
        )

        await mail_service.queue(template=template, email_data=email_data)

        mock_queue_service.push.assert_called_once_with(
            task=SendEmail,
            data={
                'content': 'test_render',
                'email_data': email_data,
            },
        )
