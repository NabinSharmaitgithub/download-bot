from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.handlers.about import about_command
from app.bot.handlers.admin import admin_command
from app.bot.handlers.cancel import cancel_command
from app.bot.handlers.help import help_command
from app.bot.handlers.history import history_command
from app.bot.handlers.language import language_command
from app.bot.handlers.queue import queue_command
from app.bot.handlers.settings import settings_command
from app.bot.handlers.start import start_command
from app.bot.handlers.status import status_command


def setup_routers(dp) -> None:
    main_router = Router()

    main_router.message.register(start_command, Command("start"))
    main_router.message.register(help_command, Command("help"))
    main_router.message.register(settings_command, Command("settings"))
    main_router.message.register(history_command, Command("history"))
    main_router.message.register(queue_command, Command("queue"))
    main_router.message.register(status_command, Command("status"))
    main_router.message.register(cancel_command, Command("cancel"))
    main_router.message.register(about_command, Command("about"))
    main_router.message.register(language_command, Command("language"))
    main_router.message.register(admin_command, Command("admin"))

    dp.include_router(main_router)