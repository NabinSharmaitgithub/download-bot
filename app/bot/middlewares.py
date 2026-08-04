import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from aiogram.types import User as TelegramUser

from app.core.localization import get_localization
from app.core.logging import get_logger, structlog

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        start_time = time.perf_counter()
        update: Update = data.get("event_update")
        user: TelegramUser | None = data.get("event_from_user")

        if update:
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(
                update_id=update.update_id,
                user_id=user.id if user else None,
            )

        try:
            result = await handler(event, data)
            return result
        except Exception as e:
            logger.exception(
                "middleware_error",
                update_type=type(event).__name__,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise
        finally:
            duration = time.perf_counter() - start_time
            logger.debug(
                "update_processed",
                update_type=type(event).__name__,
                duration_ms=round(duration * 1000, 2),
            )


class LocalizationMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.i18n = get_localization()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: TelegramUser | None = data.get("event_from_user")
        locale = "en"
        if user and hasattr(user, "language_code") and user.language_code:
            locale = user.language_code.split("-")[0].lower()
            if locale not in self.i18n.available_locales:
                locale = "en"

        data["i18n"] = self.i18n
        data["locale"] = locale
        structlog.contextvars.bind_contextvars(user_locale=locale)

        return await handler(event, data)


class DatabaseSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from app.database import get_db_session

        async for session in get_db_session():
            data["db_session"] = session
            return await handler(event, data)


class UserRegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: TelegramUser | None = data.get("event_from_user")
        if user:
            data["telegram_user"] = user

        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 30, window: int = 60) -> None:
        self.limit = limit
        self.window = window
        self._requests: dict[int, list[float]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: TelegramUser | None = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        current_time = time.time()
        user_requests = self._requests.get(user.id, [])
        user_requests = [t for t in user_requests if current_time - t < self.window]

        if len(user_requests) >= self.limit:
            logger.warning("rate_limit_exceeded", user_id=user.id)
            from aiogram.types import Message

            if isinstance(event, Message):
                i18n = data.get("i18n")
                locale = data.get("locale", "en")
                if i18n:
                    await event.answer(i18n.get("errors.rate_limited", locale, seconds=self.window))
            return

        user_requests.append(current_time)
        self._requests[user.id] = user_requests

        return await handler(event, data)


class FloodProtectionMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 10, window: int = 10) -> None:
        self.limit = limit
        self.window = window
        self._requests: dict[int, list[float]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: TelegramUser | None = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        current_time = time.time()
        user_requests = self._requests.get(user.id, [])
        user_requests = [t for t in user_requests if current_time - t < self.window]

        if len(user_requests) >= self.limit:
            logger.warning("flood_protection_triggered", user_id=user.id)
            return

        user_requests.append(current_time)
        self._requests[user.id] = user_requests

        return await handler(event, data)


class ErrorHandlingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception(
                "unhandled_error_in_handler",
                update_type=type(event).__name__,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            from aiogram.types import Message

            if isinstance(event, Message):
                i18n = data.get("i18n")
                locale = data.get("locale", "en")
                if i18n:
                    await event.answer(i18n.get("errors.internal_error", locale))
            raise


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.middleware(ErrorHandlingMiddleware())
    dp.update.middleware(FloodProtectionMiddleware())
    dp.update.middleware(RateLimitMiddleware())
    dp.update.middleware(RequestLoggingMiddleware())
    dp.update.middleware(LocalizationMiddleware())
    dp.update.middleware(DatabaseSessionMiddleware())
    dp.update.middleware(UserRegistrationMiddleware())
    logger.info("middlewares_setup")
