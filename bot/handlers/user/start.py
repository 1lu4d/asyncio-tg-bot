"""
/start command and the main reply-keyboard menu:
  - Random note
  - All notes
  - Upload note
"""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user_kb import main_menu_kb
from bot.database.repositories.user_repo import get_or_create
from bot.utils.locale import get_user_strings

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    await message.answer(
        strings["WELCOME"],
        reply_markup=main_menu_kb(strings),
    )
