"""
Admin-only moderation queue.

Every new pending note is pushed to all configured admins (notify_admins,
called from handlers/user/upload.py) with three inline buttons:
Approve / Reject / Add note. "Add note" opens a short FSM where the
admin types free text (definition, correction, source, etc.) that gets
stored alongside the entry.
"""
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import AdminNotification, Note, NoteStatus, User
from bot.database.repositories import note_repo, notification_repo
from bot.database.repositories.language_repo import get_user_language
from bot.filters.is_admin import IsAdmin
from bot.keyboards.admin_kb import moderation_kb
from bot.states.admin_states import AdminAnnotate
from bot.utils.locale import get_user_strings, get_locale_strings

router = Router(name="moderation")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def notify_admins(bot: Bot, note: Note, session: AsyncSession) -> None:
    for admin_id in settings.admin_ids:
        admin_language = await get_user_language(session, admin_id)
        admin_strings = get_locale_strings(admin_language)
        try:
            sent = await bot.send_photo(
                admin_id,
                note.file_id,
                caption=note.caption,
                reply_markup=moderation_kb(note.id, admin_strings),
            )
            await notification_repo.add_notification(
                session, note.id, admin_id, sent.message_id
            )
        except TelegramBadRequest as exc:
            logging.warning(
                "Failed to notify admin %s: %s",
                admin_id,
                exc,
            )


async def cleanup_admin_notifications(bot: Bot, session: AsyncSession, note_id: int) -> None:
    notifications = await notification_repo.get_notifications_for_note(session, note_id)
    for notification in notifications:
        try:
            await bot.delete_message(notification.chat_id, notification.message_id)
        except TelegramBadRequest:
            pass
    await notification_repo.delete_notifications_for_note(session, note_id)


async def announce_to_channel(bot: Bot, note: Note) -> None:
    channel_id = settings.announcement_channel
    if not channel_id:
        return

    try:
        await bot.send_photo(channel_id, note.file_id, caption=note.caption)
    except TelegramBadRequest as exc:
        logging.warning(
            "Failed to post approved note to channel %s: %s",
            channel_id,
            exc,
        )


async def notify_author_about_approval(bot: Bot, session: AsyncSession, note: Note) -> None:
    author = await session.get(User, note.author_id)
    if author is None:
        return

    author_strings = get_locale_strings(author.language)
    approved_caption = note.caption or ""
    message_text = author_strings["YOUR_NOTE_APPROVED"]
    if approved_caption:
        message_text += f"\n\n{approved_caption}"

    try:
        await bot.send_photo(author.tg_id, note.file_id, caption=message_text, message_effect_id="5046509860342981630")
    except TelegramBadRequest as exc:
        logging.warning(
            "Failed to notify author %s about approval: %s",
            author.tg_id,
            exc,
        )


async def notify_author_about_rejection(bot: Bot, session: AsyncSession, note: Note) -> None:
    author = await session.get(User, note.author_id)
    if author is None:
        return

    author_strings = get_locale_strings(author.language)
    message_text = author_strings["YOUR_NOTE_REJECTED"]
    if note.admin_note:
        message_text += f"\n\n{author_strings['CAUSE_PREFIX']}{note.admin_note}"
    if note.caption:
        message_text += f"\n\n{note.caption}"

    try:
        await bot.send_photo(author.tg_id, note.file_id, caption=message_text, message_effect_id="5104995460515406168")
    except TelegramBadRequest as exc:
        logging.warning(
            "Failed to notify author %s about rejection: %s",
            author.tg_id,
            exc,
        )


@router.callback_query(F.data.startswith("mod:approve:"))
async def approve_note(callback: CallbackQuery, session: AsyncSession) -> None:
    note_id = int(callback.data.split(":")[2])
    note = await session.get(Note, note_id)
    strings = await get_user_strings(callback.message, session)
    if note is None:
        await callback.answer(strings["NOTE_NOT_FOUND"], show_alert=True)
        return
    if note.status != NoteStatus.PENDING:
        await callback.answer(strings["NOTE_ALREADY_REVIEWED"], show_alert=True)
        return

    await note_repo.set_status(session, note_id, NoteStatus.APPROVED, callback.from_user.id)
    await cleanup_admin_notifications(callback.bot, session, note_id)
    await announce_to_channel(callback.bot, note)
    await notify_author_about_approval(callback.bot, session, note)
    await callback.answer(strings["APPROVED"])


@router.callback_query(F.data.startswith("mod:reject:"))
async def reject_note(callback: CallbackQuery, session: AsyncSession) -> None:
    note_id = int(callback.data.split(":")[2])
    note = await session.get(Note, note_id)
    strings = await get_user_strings(callback.message, session)
    if note is None:
        await callback.answer(strings["NOTE_NOT_FOUND"], show_alert=True)
        return
    if note.status != NoteStatus.PENDING:
        await callback.answer(strings["NOTE_ALREADY_REVIEWED"], show_alert=True)
        return

    await note_repo.set_status(session, note_id, NoteStatus.REJECTED, callback.from_user.id)
    await cleanup_admin_notifications(callback.bot, session, note_id)
    await notify_author_about_rejection(callback.bot, session, note)
    await callback.answer(strings["REJECTED"])


@router.callback_query(F.data.startswith("mod:annotate:"))
async def start_annotate(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    strings = await get_user_strings(callback.message, session)
    note_id = int(callback.data.split(":")[2])
    await state.update_data(note_id=note_id)
    await state.set_state(AdminAnnotate.waiting_for_text)
    await callback.message.answer(strings["SEND_ANNOTATION_PROMPT"])
    await callback.answer()


@router.message(AdminAnnotate.waiting_for_text)
async def save_annotation(message: Message, state: FSMContext, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    data = await state.get_data()
    note_id = data["note_id"]
    await note_repo.add_admin_note(session, note_id, text=message.text)
    await state.clear()
    await message.answer(strings["NOTE_ATTACHED"])
