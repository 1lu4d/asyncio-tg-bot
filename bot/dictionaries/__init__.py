from bot.dictionaries import en, ru

locales = {
    "en": en.strings,
    "ru": ru.strings,
}

available_languages = {
    code: locale["LANGUAGE_NAME"]
    for code, locale in locales.items()
}
