"""
Entry point. Wires together the bot, dispatcher, middlewares and
routers, then starts long polling.

Run locally:   python -m bot.main
Run in docker: see Dockerfile / docker-compose.yml
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database.engine import init_db
from bot.handlers import get_routers
from bot.middlewares.db_session import DbSessionMiddleware


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    await init_db()  # create tables if they don't exist yet (SQLite dev-friendly path)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Injects a DB session into every update's handler data as `session`.
    dp.update.middleware(DbSessionMiddleware())

    for router in get_routers():
        dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
