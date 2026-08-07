"""Aggregates all routers so main.py only needs one import."""
from aiogram import Router

from bot.handlers.admin import moderation
from bot.handlers.user import browse, fallback, language, reactions, start, upload


def get_routers() -> list[Router]:
    # Put the language router early so its `waiting_for_language` handlers
    # can intercept commands (like /start) and clear the FSM state.
    return [
        language.router,
        start.router,
        upload.router,
        browse.router,
        reactions.router,
        moderation.router,
        fallback.router,
    ]
