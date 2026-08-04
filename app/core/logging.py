import logging
import sys
from typing import Any

import structlog
from pythonjsonlogger import jsonlogger
from structlog.types import EventDict, WrappedLogger

from app.core.config import get_settings


def add_app_context(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    settings = get_settings()
    event_dict["app_env"] = settings.app_env
    event_dict["service"] = "download-bot"
    return event_dict


def add_request_context(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    request_id = getattr(structlog.contextvars, "request_id", None)
    if request_id:
        event_dict["request_id"] = request_id
    user_id = getattr(structlog.contextvars, "user_id", None)
    if user_id:
        event_dict["user_id"] = user_id
    download_id = getattr(structlog.contextvars, "download_id", None)
    if download_id:
        event_dict["download_id"] = download_id
    return event_dict


def filter_secrets(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    secrets = {
        "token",
        "password",
        "secret",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "webhook_secret",
        "hmac_secret",
        "database_url",
        "redis_url",
    }
    for key in list(event_dict.keys()):
        if any(s in key.lower() for s in secrets):
            event_dict[key] = "***REDACTED***"
    return event_dict


def setup_logging() -> None:
    settings = get_settings()

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
        add_app_context,
        add_request_context,
        filter_secrets,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={
                "timestamp": "timestamp",
                "level": "level",
                "name": "logger",
                "message": "message",
            },
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    for logger_name in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "aiogram",
        "sqlalchemy",
        "asyncpg",
    ]:
        logging.getLogger(logger_name).handlers = [handler]
        logging.getLogger(logger_name).setLevel(log_level)
        logging.getLogger(logger_name).propagate = False


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)