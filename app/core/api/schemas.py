from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, model_serializer

from app.core.db import Pagination


@dataclass
class OmitIfNone:
    pass


class ResponseStatus(Enum):
    SUCCESS: int = 0
    ERROR: int = 1000
    INVALID_INPUT: int = 1010
    VALIDATION_ERROR: int = 1011
    NOT_FOUND_ERROR: int = 1020
    NOT_AUTHORIZED = 1030
    ACTION_NOT_ALLOWED = 1031


class ResponseMeta(BaseModel):
    pagination: Pagination


T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    code: ResponseStatus = ResponseStatus.SUCCESS
    message: str | None = None
    data: Annotated[T | None, OmitIfNone()] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.message is None:
            self.message = self.code.name.lower().replace('_', ' ')

    @model_serializer
    def _serialize(self):
        omit_if_none_fields = {
            k for k, v in self.model_fields.items() if any(isinstance(m, OmitIfNone) for m in v.metadata)
        }

        return {k: v for k, v in self if k not in omit_if_none_fields or v is not None}


class PaginatedResponse(Response, Generic[T]):
    meta: Annotated[ResponseMeta | None, OmitIfNone()] = None
