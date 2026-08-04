import asyncio

from app.bot import bot_app
from app.core.logging import setup_logging


async def main() -> None:
    setup_logging()
    await bot_app.initialize()
    try:
        await bot_app.start()
    finally:
        await bot_app.stop()


if __name__ == "__main__":
    asyncio.run(main())
