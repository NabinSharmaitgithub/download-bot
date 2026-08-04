from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.bot import bot_app, lifespan
from app.database import database


class TestBotLifecycle:
    @pytest.mark.asyncio
    async def test_bot_app_initialization(self):
        with patch("app.bot.bot_app.settings") as mock_settings:
            mock_settings.bot_mode = "polling"
            mock_settings.redis_url = None
            mock_settings.telegram_bot_token = "123456789:ABCDEF"
            mock_settings.webhook_url = None
            mock_settings.webhook_path = "/webhook"
            mock_settings.webhook_secret = None
            mock_settings.fastapi_port = 8000

            with patch("app.bot.database.initialize") as mock_db_init:
                with patch("app.bot.Bot") as mock_bot_class:
                    with patch("app.bot.MemoryStorage") as mock_storage:
                        with patch("app.bot.Dispatcher") as mock_dispatcher:
                            with patch("app.bot.setup_middlewares") as mock_setup_middlewares:
                                with patch("app.bot.setup_routers") as mock_setup_routers:
                                    mock_bot = AsyncMock()
                                    mock_bot_class.return_value = mock_bot
                                    mock_dispatcher_instance = MagicMock()
                                    mock_dispatcher.return_value = mock_dispatcher_instance

                                    await bot_app.initialize()

                                    mock_db_init.assert_called_once()
                                    mock_bot_class.assert_called_once()
                                    mock_setup_middlewares.assert_called_once_with(
                                        mock_dispatcher_instance
                                    )
                                    mock_setup_routers.assert_called_once_with(
                                        mock_dispatcher_instance
                                    )
                                    mock_bot.delete_webhook.assert_called_once_with(
                                        drop_pending_updates=True
                                    )

    @pytest.mark.asyncio
    async def test_bot_app_stop(self):
        bot_app.bot = AsyncMock()
        bot_app.dp = MagicMock()

        with patch("app.bot.database.close") as mock_db_close:
            await bot_app.stop()
            bot_app.bot.session.close.assert_called_once()
            mock_db_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_context_manager(self):
        mock_app = MagicMock()

        with patch("app.bot.bot_app.initialize") as mock_init:
            with patch("app.bot.bot_app.stop") as mock_stop:
                async with lifespan(mock_app):
                    pass

                mock_init.assert_called_once()
                mock_stop.assert_called_once()