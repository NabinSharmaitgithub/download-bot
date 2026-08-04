from aiogram.types import Message

from app.core.logging import get_logger

logger = get_logger(__name__)


async def start_command(message: Message) -> None:
    i18n = message.bot.get("i18n")
    locale = message.bot.get("locale", "en")

    if not i18n:
        from app.core.localization import get_localization

        i18n = get_localization()

    user = message.from_user
    logger.info("user_started", user_id=user.id, username=user.username)

    await message.answer(i18n.get("common.start", locale))