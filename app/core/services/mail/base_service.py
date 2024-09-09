from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.services.mail.base_template import BaseTemplate
from app.core.services.queue import QueueResult


@dataclass
class EmailData:
    subject: str
    recipient: str
    sender_address: str | None = None
    sender_name: str | None = None


class MailServiceInterface(ABC):
    @abstractmethod
    async def send(self, template: BaseTemplate, email_data: EmailData) -> None:
        raise NotImplementedError

    @abstractmethod
    async def queue(self, template: BaseTemplate, email_data: EmailData) -> QueueResult | None:
        raise NotImplementedError
