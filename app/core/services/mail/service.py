from typing import Annotated

from fastapi import Depends

from app.core.services.mail.base_service import MailServiceInterface
from app.core.services.mail.providers.aiosmtplib.service import AioSmtpLibMailService
from app.core.services.queue import QueueServiceInterface, get_queue_service


def get_mail_service(
    queue_service: Annotated[QueueServiceInterface, Depends(get_queue_service)],
) -> MailServiceInterface:
    return AioSmtpLibMailService(queue_service)
