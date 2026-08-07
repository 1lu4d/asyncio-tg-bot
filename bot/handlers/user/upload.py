"""
FSM flow for submitting a new note.

Flow:
  1. User taps "Upload note" -> bot asks for a photo with a caption.
  2. User sends a photo message (caption = the note text).
  3. Bot stores it with status=PENDING and notifies every admin for review.

Only one state is needed: Telegram lets a photo carry a caption in a
single message, so there's no separate "now send the caption" step.
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.upload_states import UploadNote
from bot.database.repositories import note_repo, user_repo
from bot.handlers.admin.moderation import notify_admins
from bot.utils.locale import get_user_strings, get_button_variants

router = Router(name="upload")


@router.message(F.text.in_(get_button_variants("UPLOAD_NOTE_BUTTON")))
@router.message(Command(commands=["submit"]))
async def start_upload(message: Message, state: FSMContext, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    await state.set_state(UploadNote.waiting_for_photo)
    await message.answer(strings["SEND_PHOTO_CAPTION_PROMPT"])


@router.message(UploadNote.waiting_for_photo, F.photo)
async def receive_photo(message: Message, state: FSMContext, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    if not message.caption or not message.caption.strip():
        await message.answer(strings["PHOTO_CAPTION_REQUIRED"])
        return

    author = await user_repo.get_or_create(
        session,
        message.from_user.id,
        message.from_user.username,
    )

    if message.from_user.username:
        caption = f"{message.caption}\n\nAuthor: @{message.from_user.username}"
    else:
        caption = f"{message.caption}\n\nAuthor: {message.from_user.first_name or 'Unknown'}"

    note = await note_repo.create_pending(
        session,
        author_id=author.id,
        file_id=message.photo[-1].file_id,
        caption=caption,
    )
    await notify_admins(message.bot, note, session)
    await state.clear()
    await message.answer(strings["NOTE_SENT_FOR_REVIEW"])


@router.message(UploadNote.waiting_for_photo, Command(commands=["cancel"]))
async def cancel_upload(message: Message, state: FSMContext, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    await state.clear()
    await message.answer(strings["UPLOAD_CANCELLED"])


@router.message(UploadNote.waiting_for_photo)
async def wrong_content_type(message: Message, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    await message.answer(strings["UPLOAD_WRONG_CONTENT_TYPE"])
