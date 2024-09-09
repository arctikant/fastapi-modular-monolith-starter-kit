from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.api import GeneralException, ResponseStatus
from app.core.deps import logger


class ExceptionHandlers:
    @staticmethod
    async def validation_exception_handler(request: Request, exc: RequestValidationError | ValidationError):
        return JSONResponse(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'code': ResponseStatus.VALIDATION_ERROR.value,
                'message': 'Validation error',
                'details': exc.errors() if isinstance(exc, ValidationError) else jsonable_encoder(exc.errors()),
            },
        )

    @staticmethod
    async def general_api_exception_handler(request: Request, exc: GeneralException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'code': exc.status.value,
                'message': exc.message,
            },
        )

    @staticmethod
    async def general_exception_handler(request: Request, exc: Exception):
        await logger.a_exception('unhandled_exception')

        return JSONResponse(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'code': ResponseStatus.ERROR.value,
                'message': 'An internal server error occurred. Please try again later.',
            },
        )

    @staticmethod
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == http_status.HTTP_404_NOT_FOUND:
            return await ExceptionHandlers.not_found_exception_handler(request, exc)
        elif exc.status_code == http_status.HTTP_401_UNAUTHORIZED:
            return await ExceptionHandlers.unauthorized_exception_handler(request, exc)

        # Handle other HTTP exceptions here or return a default response
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'code': ResponseStatus.ERROR.value,
                'message': str(exc.detail),
            },
        )

    @staticmethod
    async def unauthorized_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'code': ResponseStatus.NOT_AUTHORIZED.value,
                'message': 'Not authorized',
            },
        )

    @staticmethod
    async def not_found_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'code': ResponseStatus.NOT_FOUND_ERROR.value,
                'message': exc.detail or 'The requested resource was not found.',
            },
        )

    @staticmethod
    def get_handlers():
        return {
            RequestValidationError: ExceptionHandlers.validation_exception_handler,
            ValidationError: ExceptionHandlers.validation_exception_handler,
            StarletteHTTPException: ExceptionHandlers.http_exception_handler,
            GeneralException: ExceptionHandlers.general_api_exception_handler,
            Exception: ExceptionHandlers.general_exception_handler,
        }
