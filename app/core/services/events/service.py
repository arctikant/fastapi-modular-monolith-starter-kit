from typing import Any

from app.core.services.events.base_service import EventsServiceInterface
from app.core.services.events.providers.fastapi_events.decorators import (
    LocalListenerDecorator,
)
from app.core.services.events.providers.fastapi_events.service import (
    FastAPIEventsService,
)


def get_events_service() -> EventsServiceInterface:
    return FastAPIEventsService()


def get_listener_decorator() -> Any:
    return LocalListenerDecorator()
