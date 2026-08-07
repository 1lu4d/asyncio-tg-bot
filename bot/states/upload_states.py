from aiogram.fsm.state import State, StatesGroup


class UploadNote(StatesGroup):
    # A photo message can carry its own caption, so a single state
    # covers the whole user-facing upload flow - no multi-step wizard needed.
    waiting_for_photo = State()
