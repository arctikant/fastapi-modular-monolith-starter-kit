import logging.config

import structlog

from app.core.configs import app_config

logging.config.dictConfig(
    {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'plain': {
                '()': 'logging.Formatter',
                'fmt': '[%(asctime)s] %(levelname)-8s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'json': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processors': [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()],
            },
        },
        'handlers': {
            'stream': {
                'formatter': 'plain',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stderr',
            },
            'file': {
                'formatter': 'plain',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': 'logs/app.log',
                'when': 'midnight',
                'utc': True,
                'delay': True,
                'backupCount': 7,
            },
        },
        'loggers': {
            'main': {'handlers': app_config.LOG_HANDLERS, 'level': app_config.LOG_LEVEL},
        },
    }
)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        # structlog.processors.StackInfoRenderer(),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger('main')
