from __future__ import annotations

from typing import Any

from aiogram import F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.dictionaries import locales, available_languages
from bot.database.repositories.language_repo import get_user_language, set_user_language
from bot.database.repositories.user_repo import get_or_create

DEFAULT_LANGUAGE = "en"


def get_locale_strings(language_code: str | None) -> dict[str, str]:
    if language_code and language_code in locales:
        return locales[language_code]
    return locales[DEFAULT_LANGUAGE]


def get_button_variants(key: str) -> list[str]:
    return [locale[key] for locale in locales.values() if key in locale]


async def get_user_strings(message: Message, session: AsyncSession) -> dict[str, str]:
    await get_or_create(session, message.from_user.id, message.from_user.username)
    language = await get_user_language(session, message.from_user.id)
    return get_locale_strings(language)


async def set_language_for_user(session: AsyncSession, message: Message, language: str) -> str:
    if language not in locales:
        return "unsupported"
    await set_user_language(session, message.from_user.id, language)
    return language


def language_keyboard() -> list[list[str]]:
    return [[f"{code} - {name}"] for code, name in available_languages.items()]
