from aiogram.types import Message

from app.core.logging import get_logger

logger = get_logger(__name__)


async def queue_command(message: Message) -> None:
    i18n = message.bot.get("i18n")
    locale = message.bot.get("locale", "en")

    if not i18n:
        from app.core.localization import get_localization

        i18n = get_localization()

    await message.answer(i18n.get("queue.empty", locale))