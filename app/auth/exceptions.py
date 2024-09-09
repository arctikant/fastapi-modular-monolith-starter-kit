from fastapi import status as http_status

from app.core.api import GeneralException, ResponseStatus


class InvalidInput(GeneralException):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(
            message=message,
            status_code=(status_code or http_status.HTTP_400_BAD_REQUEST),
            status=ResponseStatus.INVALID_INPUT,
        )


class ActionNotAllowed(GeneralException):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(
            message=message,
            status_code=(status_code or http_status.HTTP_403_FORBIDDEN),
            status=ResponseStatus.ACTION_NOT_ALLOWED,
        )
