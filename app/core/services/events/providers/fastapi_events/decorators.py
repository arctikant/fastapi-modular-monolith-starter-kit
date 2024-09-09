from collections.abc import Callable
from functools import wraps

from fastapi_events.handlers.local import local_handler

from app.core.services.events import ListenedEvent
from app.core.services.events.base_event import BaseEvent


class LocalListenerDecorator:
    def __call__(self, cls: type[BaseEvent]) -> Callable:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args) -> ListenedEvent:
                return func(ListenedEvent(name=args[0][0], data=args[0][1]))

            local_handler.register(_func=func, event_name=cls.get_name())

            return wrapper

        return decorator
