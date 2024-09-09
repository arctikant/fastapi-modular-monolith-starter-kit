from pydantic import EmailStr

from app.core.services.events import BaseEvent


class UserCreated(BaseEvent):
    __event_name__ = 'user_created'

    id: int
    email: EmailStr
    username: str


class UserDeleted(BaseEvent):
    __event_name__ = 'user_deleted'

    id: int
