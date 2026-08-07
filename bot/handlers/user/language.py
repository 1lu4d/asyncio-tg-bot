from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user_kb import language_menu_kb, main_menu_kb
from bot.utils.locale import (
    available_languages,
    get_button_variants,
    get_locale_strings,
    get_user_strings,
    set_language_for_user,
)

router = Router(name="language")


class LanguageSelection(StatesGroup):
    waiting_for_language = State()


@router.message(F.text.in_(get_button_variants("LANGUAGE_BUTTON")))
@router.message(Command(commands=["language"]))
async def language_command(message: Message, session: AsyncSession, state: FSMContext) -> None:
    strings = await get_user_strings(message, session)
    await state.set_state(LanguageSelection.waiting_for_language)
    await message.answer(strings["LANGUAGE_PICK_PROMPT"], reply_markup=language_menu_kb())

@router.message(LanguageSelection.waiting_for_language, F.text.regexp(r"^[a-z]{2}(?:\s*-.*)?$", flags=0))
async def choose_language(message: Message, session: AsyncSession, state: FSMContext) -> None:
    text = message.text.strip()
    if "-" in text:
        selected_code = text.split("-", 1)[0].strip().lower()
    else:
        selected_code = text.lower()

    current_strings = await get_user_strings(message, session)
    result = await set_language_for_user(session, message, selected_code)
    if result == "unsupported":
        await message.answer(current_strings["LANGUAGE_NOT_SUPPORTED"])
        await state.clear()
        return

    await state.clear()
    language_name = available_languages.get(result, result)
    strings = get_locale_strings(result)
    await message.answer(
        strings["LANGUAGE_CHANGED"].format(language=language_name),
        reply_markup=main_menu_kb(strings),
    )


@router.message(LanguageSelection.waiting_for_language)
async def cancel_waiting_on_other_input(message: Message, session: AsyncSession, state: FSMContext) -> None:
    # If the user does anything other than a valid language selection,
    # clear the waiting state so the bot stops expecting a language.
    strings = await get_user_strings(message, session)
    await state.clear()
    await message.answer(strings.get("LANGUAGE_CANCELLED", "Language selection cancelled."), reply_markup=main_menu_kb(strings))
    
@router.message(LanguageSelection.waiting_for_language, Command(commands=["cancel"]))
async def cancel_language_selection(message: Message, state: FSMContext, session: AsyncSession) -> None:
    strings = await get_user_strings(message, session)
    await state.clear()
    await message.answer(strings["UPLOAD_CANCELLED"])