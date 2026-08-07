import pytest

from bot.dictionaries import available_languages
from bot.utils.locale import get_button_variants, get_locale_strings


def test_available_languages_contains_known_codes() -> None:
    assert "en" in available_languages
    assert "ru" in available_languages


def test_get_button_variants_returns_localized_buttons() -> None:
    variants = get_button_variants("RANDOM_NOTE_BUTTON")
    assert "🎲 Random note" in variants
    assert "🎲 Случайная заметка" in variants


def test_get_locale_strings_defaults_to_english_for_unknown_code() -> None:
    strings = get_locale_strings("xx")
    assert strings["LANGUAGE_NAME"] == "English"
    assert strings["WELCOME"].startswith("Welcome")
