from unittest.mock import Mock, patch

from app.core.services.events import BaseEvent
from app.core.services.events.providers.fastapi_events.service import (
    FastAPIEventsService,
)


class StubEvent(BaseEvent):
    __event_name__ = 'stub_event'


class TestFastAPIEventsService:
    @patch('app.core.services.events.providers.fastapi_events.service.dispatch')
    def test_dispatch(self, mock_dispatch: Mock) -> None:
        test_event = StubEvent()
        events_service = FastAPIEventsService()
        events_service.dispatch(test_event)

        mock_dispatch.assert_called_once_with(test_event)
