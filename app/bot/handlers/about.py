from aiogram.types import Message

from app.core.logging import get_logger

logger = get_logger(__name__)


async def about_command(message: Message) -> None:
    i18n = message.bot.get("i18n")
    locale = message.bot.get("locale", "en")

    if not i18n:
        from app.core.localization import get_localization

        i18n = get_localization()

    await message.answer(
        f"Download Bot v0.1.0\n"
        f"Multi-provider download bot for Telegram\n\n"
        f"Supported providers:\n"
        f"- YouTube\n"
        f"- Google Drive\n"
        f"- Dropbox\n"
        f"- TeraBox"
    )
