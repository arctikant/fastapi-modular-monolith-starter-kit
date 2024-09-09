from fastapi_events.dispatcher import dispatch

from app.core.services.events.base_event import BaseEvent
from app.core.services.events.base_service import EventsServiceInterface


class FastAPIEventsService(EventsServiceInterface):
    def dispatch(self, event: BaseEvent) -> None:
        dispatch(event)
