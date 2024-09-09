from email.message import EmailMessage

import aiosmtplib

from app.core.configs import app_config
from app.core.services.mail.base_service import EmailData, MailServiceInterface
from app.core.services.mail.base_template import BaseTemplate
from app.core.services.mail.providers.aiosmtplib.setup import smtp_config
from app.core.services.mail.providers.aiosmtplib.tasks import SendEmail
from app.core.services.queue import QueueResult, QueueServiceInterface


class AioSmtpLibMailService(MailServiceInterface):
    def __init__(self, queue_service: QueueServiceInterface) -> None:
        assert app_config.emails_configured, 'Required Email configuration parameters are not set'

        self._queue_service = queue_service

    async def send(self, template: BaseTemplate, email_data: EmailData) -> None:
        sender_name = email_data.sender_name or app_config.EMAIL_SENDER_NAME
        sender_address = email_data.sender_address or app_config.EMAIL_SENDER_ADDRESS

        message = EmailMessage()
        message['From'] = f'{sender_name} <{sender_address}>'
        message['To'] = email_data.recipient
        message['Subject'] = f'{app_config.PROJECT_NAME} | {email_data.subject}'
        message.add_alternative(template.render(), subtype='html')

        await aiosmtplib.send(message, **smtp_config)

    async def queue(self, template: BaseTemplate, email_data: EmailData) -> QueueResult | None:
        return await self._queue_service.push(
            task=SendEmail,
            data={'content': template.render(), 'email_data': email_data},
        )
