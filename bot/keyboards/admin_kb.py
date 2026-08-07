"""Inline keyboard attached to each pending note sent to admins."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def moderation_kb(note_id: int, strings: dict[str, str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=strings.get("APPROVE_BUTTON", "✅ Approve"), callback_data=f"mod:approve:{note_id}"),
                InlineKeyboardButton(text=strings.get("REJECT_BUTTON", "❌ Reject"), callback_data=f"mod:reject:{note_id}"),
            ],
            [InlineKeyboardButton(text=strings.get("ANNOTATE_BUTTON", "📝 Add note"), callback_data=f"mod:annotate:{note_id}")],
        ]
    )
