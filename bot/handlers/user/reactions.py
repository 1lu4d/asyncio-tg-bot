"""
Reaction buttons under each note.

Callback data format: "react:<note_id>:<reaction_emoji>"
Actual toggle/replace logic lives in reaction_repo.set_reaction() -
this handler just calls it and re-renders the updated counts.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import reaction_repo
from bot.keyboards.user_kb import note_navigation_kb, reaction_only_kb
from bot.utils.locale import get_user_strings

router = Router(name="reactions")


@router.callback_query(F.data.startswith("react:"))
async def handle_reaction(callback: CallbackQuery, session: AsyncSession) -> None:
    _, note_id, reaction = callback.data.split(":")
    note_id = int(note_id)

    await reaction_repo.set_reaction(
        session,
        note_id=note_id,
        user_id=callback.from_user.id,
        reaction=reaction,
    )

    counts = await reaction_repo.get_counts(session, note_id)
    if callback.message and callback.message.reply_markup:
        inline_kb = callback.message.reply_markup.inline_keyboard
        if inline_kb and inline_kb[0] and inline_kb[0][0].callback_data.startswith("nav:"):
            await callback.message.edit_reply_markup(reply_markup=note_navigation_kb(note_id, counts))
        else:
            await callback.message.edit_reply_markup(reply_markup=reaction_only_kb(note_id, counts))

    # Localize the confirmation for the *reactor*, not the message author.
    # `callback.message.from_user` is the bot/message author; use `callback.from_user`.
    class _MsgLike:
        def __init__(self, user):
            self.from_user = user

    fake_msg = _MsgLike(callback.from_user)
    strings = await get_user_strings(fake_msg, session)
    await callback.answer(strings.get("REACTION_SAVED", "Reaction saved!"))
