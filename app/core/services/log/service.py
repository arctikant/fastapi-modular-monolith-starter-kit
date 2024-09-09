from app.core.services.log.base_service import LogServiceInterface
from app.core.services.log.providers.structlog.service import StructLogService
from app.core.services.log.providers.structlog.setup import logger


def get_log_service() -> LogServiceInterface:
    return StructLogService(logger)
