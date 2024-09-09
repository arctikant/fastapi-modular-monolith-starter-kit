from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.services.cache import (
    CacheServiceInterface,
    get_cache_service,
    get_cached_decorator,
)
from app.core.services.events import (
    EventsServiceInterface,
    get_events_service,
    get_listener_decorator,
)
from app.core.services.log import get_log_service
from app.core.services.mail import MailServiceInterface, get_mail_service
from app.core.services.queue import QueueServiceInterface, get_queue_service
from app.core.services.queue.service import get_queued_decorator

# Singleton

logger = get_log_service()

# Dependencies

DBSession = Annotated[AsyncSession, Depends(get_session)]
QueueService = Annotated[QueueServiceInterface, Depends(get_queue_service)]
MailService = Annotated[MailServiceInterface, Depends(get_mail_service)]
CacheService = Annotated[CacheServiceInterface, Depends(get_cache_service)]
EventsService = Annotated[EventsServiceInterface, Depends(get_events_service)]

# Decorators

cached = get_cached_decorator()
queued = get_queued_decorator()
listener = get_listener_decorator()
