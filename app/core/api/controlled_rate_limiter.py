from fastapi_limiter.depends import RateLimiter
from starlette.requests import Request
from starlette.responses import Response

from app.core.configs import app_config


class ConfigurableRateLimiter(RateLimiter):
    async def __call__(self, request: Request, response: Response):
        if app_config.RATE_LIMITER_ENABLED:
            await super().__call__(request=request, response=response)
