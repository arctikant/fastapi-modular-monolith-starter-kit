from app.core.api.schemas import ResponseStatus


class GeneralException(Exception):
    def __init__(self, message: str, status_code: int, status: ResponseStatus = ResponseStatus.ERROR):
        self.message = message
        self.status_code = status_code
        self.status = status
