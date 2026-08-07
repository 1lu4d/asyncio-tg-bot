"""Fallback handler for unrecognized user messages."""

from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.locale import get_user_strings

router = Router(name="fallback")

@router.message(Command(commands=["help"]))
async def unknown_command(message: Message, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    await message.answer(strings["HELP_TEXT"] if strings else "No one will help", parse_mode="HTML")

@router.message(F.text.startswith("/"))
async def unknown_command(message: Message, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    await message.answer(strings["UNKNOWN_COMMAND_REPLY"])


@router.message(F.text)
async def unknown_message(message: Message, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    await message.answer(strings["UNKNOWN_TEXT_REPLY"])


@router.message(F.photo)
async def unknown_photo(message: Message, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    await message.answer(strings["UNKNOWN_IMAGE_REPLY"])


@router.message()
async def unknown_media(message: Message, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    await message.answer(strings["UNKNOWN_TEXT_REPLY"])
