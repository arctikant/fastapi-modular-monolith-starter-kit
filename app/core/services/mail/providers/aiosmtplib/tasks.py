from email.message import EmailMessage

import aiosmtplib

from app.core.configs import app_config
from app.core.services.mail.providers.aiosmtplib.setup import smtp_config
from app.core.services.queue import BaseTask, get_queued_decorator

queued = get_queued_decorator()


@queued
class SendEmail(BaseTask):
    __task_name__ = 'mail.send'

    async def run(self, content: str, email_data: dict) -> None:
        sender_name = email_data['sender_name'] or app_config.EMAIL_SENDER_NAME
        sender_address = email_data['sender_address'] or app_config.EMAIL_SENDER_ADDRESS

        message = EmailMessage()
        message['From'] = f'{sender_name} <{sender_address}>'
        message['To'] = email_data['recipient']
        message['Subject'] = f'{app_config.PROJECT_NAME} | {email_data['subject']}'
        message.add_alternative(content, subtype='html')

        await aiosmtplib.send(message, **smtp_config)
