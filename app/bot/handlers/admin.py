from aiogram.types import Message

from app.core.config import get_settings
from app.core.localization import get_localization
from app.core.logging import get_logger

logger = get_logger(__name__)


async def admin_command(message: Message) -> None:
    settings = get_settings()
    i18n = message.bot.get("i18n")
    locale = message.bot.get("locale", "en")

    if not i18n:
        i18n = get_localization()

    user = message.from_user
    if not user or user.id not in settings.admin_ids:
        await message.answer(i18n.get("errors.permission_denied", locale))
        return

    await message.answer(i18n.get("admin.title", locale))
