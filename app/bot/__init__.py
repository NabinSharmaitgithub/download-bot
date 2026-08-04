from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.bot.middlewares import setup_middlewares
from app.bot.routers import setup_routers
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database import database

logger = get_logger(__name__)


class BotApp:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self._web_app: web.Application | None = None

    async def initialize(self) -> None:
        setup_logging()
        logger.info("bot_initializing", mode=self.settings.bot_mode)

        database.initialize()

        self.bot = Bot(
            token=self.settings.telegram_bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

        if self.settings.redis_url and not self.settings.is_testing:
            storage = RedisStorage.from_url(self.settings.redis_url)
        else:
            storage = MemoryStorage()

        self.dp = Dispatcher(storage=storage)

        setup_middlewares(self.dp)
        setup_routers(self.dp)

        if self.settings.bot_mode == "webhook":
            await self._setup_webhook()
        else:
            await self._setup_polling()

        logger.info("bot_initialized", mode=self.settings.bot_mode)

    async def _setup_webhook(self) -> None:
        assert self.bot is not None
        assert self.dp is not None

        webhook_url = self.settings.webhook_url
        if not webhook_url:
            raise ValueError("WEBHOOK_URL is required for webhook mode")

        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.bot.set_webhook(
            url=f"{webhook_url}{self.settings.webhook_path}",
            secret_token=self.settings.webhook_secret,
            allowed_updates=self.dp.resolve_used_update_types(),
        )
        logger.info("webhook_set", url=webhook_url)

        self._web_app = web.Application()
        SimpleRequestHandler(
            dispatcher=self.dp,
            bot=self.bot,
            secret_token=self.settings.webhook_secret,
        ).register(self._web_app, path=self.settings.webhook_path)
        setup_application(self._web_app, self.dp, bot=self.bot)

    async def _setup_polling(self) -> None:
        assert self.bot is not None
        assert self.dp is not None

        await self.bot.delete_webhook(drop_pending_updates=True)
        logger.info("polling_mode_enabled")

    async def start(self) -> None:
        logger.info("bot_starting")
        if self.settings.bot_mode == "webhook" and self._web_app:
            runner = web.AppRunner(self._web_app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", self.settings.fastapi_port)
            await site.start()
            logger.info("webhook_server_started", port=self.settings.fastapi_port)
        else:
            assert self.dp is not None
            assert self.bot is not None
            await self.dp.start_polling(self.bot)

    async def stop(self) -> None:
        logger.info("bot_stopping")
        if self.bot:
            await self.bot.session.close()
        await database.close()
        logger.info("bot_stopped")


bot_app = BotApp()


@asynccontextmanager
async def lifespan(app) -> AsyncGenerator[None]:
    await bot_app.initialize()
    yield
    await bot_app.stop()