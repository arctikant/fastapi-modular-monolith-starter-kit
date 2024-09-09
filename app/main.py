from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_events.handlers.local import local_handler
from fastapi_events.middleware import EventHandlerASGIMiddleware
from fastapi_limiter import FastAPILimiter
from starlette.middleware.cors import CORSMiddleware

# This import is necessary to proper loading of listeners
from app.core import listeners  # noqa: F401
from app.core.configs import app_config
from app.core.exception_handlers import ExceptionHandlers
from app.core.middlewares import LoggingMiddleware
from app.core.routers import router_v1


# Make necessary actions on app startup and shutdown
@asynccontextmanager
async def lifespan(app_instance: FastAPI):  # noqa: ARG001
    # Initialization and shutdown of FastAPILimiter with redis backend
    redis_client = redis.from_url(app_config.redis_url)
    await FastAPILimiter.init(redis_client)
    yield
    await redis_client.aclose()


# Create FastAPI app
app = FastAPI(
    openapi_url=f'{app_config.API_V1_STR}/openapi.json' if app_config.ENVIRONMENT in ['local', 'staging'] else None,
    lifespan=lifespan,
)

# Register middlewares

# API requests logging
app.add_middleware(LoggingMiddleware)

# Registering events local handler
app.add_middleware(EventHandlerASGIMiddleware, handlers=[local_handler])

# Set all CORS enabled origins
if app_config.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip('/') for origin in app_config.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

# Register exception handlers

for exception_class, handler in ExceptionHandlers.get_handlers().items():
    app.add_exception_handler(exception_class, handler)

# Register routers
app.include_router(router_v1, prefix=app_config.API_V1_STR)
