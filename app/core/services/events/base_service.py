from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.core.services.events.base_event import BaseEvent


@dataclass
class ListenedEvent:
    name: str
    data: Any


class EventsServiceInterface(ABC):
    @abstractmethod
    def dispatch(self, event: BaseEvent) -> None:
        raise NotImplementedError
