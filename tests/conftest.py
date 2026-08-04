import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.core.localization import Localization


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF")
    monkeypatch.setenv("SECRET_KEY", "a" * 32)
    monkeypatch.setenv("DOWNLOAD_LINK_HMAC_SECRET", "b" * 32)
    monkeypatch.setenv("APP_ENV", "testing")

    return Settings()


@pytest.fixture
def mock_localization():
    i18n = Localization(default_locale="en")
    i18n._translations = {
        "en": {
            "common": {"start": "Welcome!", "help": "Help text"},
            "errors": {"internal_error": "Internal error"},
            "settings_menu": {"title": "Settings"},
            "history": {"empty": "No history"},
            "queue": {"empty": "Queue empty"},
        },
        "ne": {
            "common": {"start": "\u0938\u094d\u0935\u093e\u0917\u0924 \u091b!", "help": "\u0938\u0939\u093e\u092f\u0924\u093e \u092a\u093e\u0920"},
            "errors": {"internal_error": "\u0906\u0928\u094d\u0924\u0930\u093f\u0915 \u0924\u094d\u0930\u0941\u091f\u093f"},
        },
    }
    return i18n


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.get = MagicMock(return_value=None)
    return bot


@pytest.fixture
def mock_message(mock_bot, mock_localization):
    message = AsyncMock()
    message.bot = mock_bot
    message.from_user = MagicMock(id=12345, username="testuser", language_code="en")
    message.chat = MagicMock(id=12345, type="private")
    message.answer = AsyncMock()
    message.bot.get = MagicMock(side_effect=lambda k: mock_localization if k == "i18n" else "en")
    return message