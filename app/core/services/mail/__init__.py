from app.core.services.mail.base_service import EmailData, MailServiceInterface
from app.core.services.mail.base_template import BaseTemplate
from app.core.services.mail.service import get_mail_service

__all__ = [
    'MailServiceInterface',
    'BaseTemplate',
    'EmailData',
    'get_mail_service',
]
