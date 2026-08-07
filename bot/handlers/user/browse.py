"""
"Random note" and "All notes" browsing.

"All notes" uses inline pagination: prev/next buttons plus the
reaction row underneath, all in one inline keyboard. Callback data
encodes the current note id so a single handler can edit the existing
message (edit_media) rather than sending a new message each time.
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from bot.config import settings

from bot.database.repositories import note_repo, reaction_repo
from bot.keyboards.user_kb import note_navigation_kb, reaction_only_kb
from bot.utils.locale import get_user_strings, get_button_variants
from bot.utils.pagination import get_adjacent_approved_note, get_first_approved_note
from bot.database.repositories.note_repo import get_approved_note_position

router = Router(name="browse")


@router.message(F.text.in_(get_button_variants("RANDOM_NOTE_BUTTON")))
@router.message(Command(commands=["random"]))
async def random_note(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """Send a random approved note.

    If a prior random note message exists we delete it first so a new
    request never edits an unrelated/older bot message.
    """
    state_data = await state.get_data()
    recent_notes = state_data.get("recent_random_notes", [])
    previous_message_id = state_data.get("last_random_message_id")

    approved_count = await note_repo.count_approved(session)
    exclude_ids: list[int] = []
    if approved_count >= 3:
        if len(recent_notes) >= 2 and len(set(recent_notes[-2:])) == 2:
            exclude_ids = recent_notes[-2:]
        elif recent_notes:
            exclude_ids = [recent_notes[-1]]
    elif approved_count == 2 and recent_notes:
        exclude_ids = [recent_notes[-1]]

    strings = await get_user_strings(message, session)
    note = await note_repo.get_random_approved_excluding(session, exclude_ids)
    if note is None:
        await message.answer(strings["NO_APPROVED_NOTES"])
        return

    counts = await reaction_repo.get_counts(session, note.id)

    # Prefer editing the previous random message when it's very recent,
    # otherwise delete it and send a new message. This avoids editing an
    # unrelated older bot message if the user interacted elsewhere.
    edited = False
    prev_ts = state_data.get("last_random_message_ts")
    now_ts = datetime.now(timezone.utc).timestamp()
    # Consider recent if within configured threshold
    RECENT_SECONDS = settings.recent_random_message_seconds
    if previous_message_id is not None and prev_ts is not None and (now_ts - float(prev_ts)) <= RECENT_SECONDS:
        try:
            await message.bot.edit_message_media(
                chat_id=message.chat.id,
                message_id=previous_message_id,
                media=InputMediaPhoto(media=note.file_id, caption=note.caption),
                reply_markup=reaction_only_kb(note.id, counts),
            )
            edited = True
        except TelegramBadRequest:
            edited = False

    if not edited:
        # If edit was not attempted or failed, try deleting the old message
        # (ignore failures) and send a fresh one.
        if previous_message_id is not None:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=previous_message_id)
            except TelegramBadRequest:
                pass

        sent_message = await message.answer_photo(
            note.file_id,
            caption=note.caption,
            reply_markup=reaction_only_kb(note.id, counts),
        )
        previous_message_id = sent_message.message_id
        prev_ts = sent_message.date.timestamp()
    else:
        # If we successfully edited, update the timestamp to now.
        prev_ts = now_ts

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    recent_notes = (recent_notes + [note.id])[-2:]
    await state.update_data(
        recent_random_notes=recent_notes,
        last_random_message_id=previous_message_id,
        last_random_message_ts=prev_ts,
    )


@router.message(F.text.in_(get_button_variants("BROWSE_NOTES_BUTTON")))
@router.message(Command(commands=["browse"]))
async def all_notes_start(message: Message, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    note = await note_repo.get_random_approved(session)
    if note is None:
        await message.answer(strings["NO_APPROVED_NOTES"])
        return

    counts = await reaction_repo.get_counts(session, note.id)
    position = await note_repo.get_approved_note_position(session, note.id)
    total = await note_repo.count_approved(session)
    page_text = f"{position}/{total}"
    await message.answer_photo(
        note.file_id,
        caption=note.caption,
        reply_markup=note_navigation_kb(note.id, counts, page_text=page_text),
    )


@router.callback_query(F.data.startswith("nav:"))
async def paginate_notes(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    # Prevent concurrent navigation edits which can cause Telegram to freeze
    # if many rapid edits are attempted. Use a per-user in-flight lock.
    data = await state.get_data()
    strings = await get_user_strings(callback.message, session) if callback.message else None
    if data.get("browse_in_flight"):
        await callback.answer(strings["PLEASE_WAIT"] if strings else "Please wait…")
        return

    await state.update_data(browse_in_flight=True)
    try:
        # callback.data format: "nav:<direction>:<current_note_id>"
        _, direction, current_id = callback.data.split(":")
        note = await get_adjacent_approved_note(session, int(current_id), direction)
        if note is None:
            await callback.answer(strings["NO_MORE_NOTES"] if strings else "No more notes.", show_alert=True)
            return

        counts = await reaction_repo.get_counts(session, note.id)
        position = await note_repo.get_approved_note_position(session, note.id)
        total = await note_repo.count_approved(session)
        page_text = f"{position}/{total}"
        if callback.message:
            try:
                await callback.message.edit_media(
                    InputMediaPhoto(media=note.file_id, caption=note.caption),
                    reply_markup=note_navigation_kb(note.id, counts, page_text=page_text),
                )
            except TelegramBadRequest:
                # Ignore transient edit failures
                pass

        await callback.answer()
    finally:
        await state.update_data(browse_in_flight=False)


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()
