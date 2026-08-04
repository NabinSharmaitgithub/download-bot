from aiogram.types import Message

from app.core.localization import get_localization
from app.core.logging import get_logger

logger = get_logger(__name__)


async def language_command(message: Message) -> None:
    i18n = message.bot.get("i18n")
    locale = message.bot.get("locale", "en")

    if not i18n:
        i18n = get_localization()

    available = ", ".join(i18n.available_locales)
    await message.answer(
        f"{i18n.get('common.language', locale)}: {locale}\n" f"Available: {available}"
    )