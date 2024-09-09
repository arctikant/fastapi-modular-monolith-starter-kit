from unittest.mock import Mock, patch

from app.core.services.events.base_event import BaseEvent
from app.core.services.events.providers.fastapi_events.decorators import (
    LocalListenerDecorator,
)


class StubEvent(BaseEvent):
    __event_name__ = 'stub_event'


class TestLocalListenerDecorator:
    @patch('app.core.services.events.providers.fastapi_events.decorators.local_handler')
    def test_call(self, mock_local_handler: Mock) -> None:
        listener = LocalListenerDecorator()

        @listener(StubEvent)
        def test_function() -> None:
            pass

        # Check if register was called
        mock_local_handler.register.assert_called_once()
        call_args = mock_local_handler.register.call_args

        assert call_args.kwargs['event_name'] == 'stub_event'
        assert call_args.kwargs['_func'].__name__ == 'test_function'
