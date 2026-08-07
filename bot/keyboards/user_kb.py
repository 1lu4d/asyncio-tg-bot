"""
Reply keyboard for the main menu + inline keyboards for browsing notes
and reacting to them. All keyboard-building logic lives here so
handlers stay focused on flow, not layout.
"""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# The defined reaction set. Change it here and it updates everywhere.
REACTIONS = ["👍", "❤️", "😂", "😮", "😢"]


def main_menu_kb(strings: dict[str, str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=strings["RANDOM_NOTE_BUTTON"]), KeyboardButton(text=strings["BROWSE_NOTES_BUTTON"])],
            [KeyboardButton(text=strings["UPLOAD_NOTE_BUTTON"]), KeyboardButton(text=strings["LANGUAGE_BUTTON"])],
        ],
        resize_keyboard=True,
    )


def reaction_row(note_id: int, counts: dict[str, int] | None = None) -> list[InlineKeyboardButton]:
    counts = counts or {}
    return [
        InlineKeyboardButton(text=f"{r} {counts.get(r, 0)}", callback_data=f"react:{note_id}:{r}")
        for r in REACTIONS
    ]


def note_navigation_kb(
    note_id: int,
    counts: dict[str, int] | None = None,
    page_text: str | None = None,
) -> InlineKeyboardMarkup:
    """Used for 'All notes' browsing: prev/next row + pager + reaction row underneath."""
    nav_row = [
        InlineKeyboardButton(text="⬅️", callback_data=f"nav:prev:{note_id}"),
        InlineKeyboardButton(text=page_text or "", callback_data="ЧёСмотришь?Хакердофига?"),
        InlineKeyboardButton(text="➡️", callback_data=f"nav:next:{note_id}"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[nav_row, reaction_row(note_id, counts)])


def reaction_only_kb(note_id: int, counts: dict[str, int] | None = None) -> InlineKeyboardMarkup:
    """Used for 'Random note': just the reaction row, no prev/next."""
    return InlineKeyboardMarkup(inline_keyboard=[reaction_row(note_id, counts)])


def language_menu_kb() -> ReplyKeyboardMarkup:
    from bot.utils.locale import available_languages

    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"{code} - {name}")] for code, name in available_languages.items()],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
