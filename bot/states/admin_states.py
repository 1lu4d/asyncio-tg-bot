from aiogram.fsm.state import State, StatesGroup


class AdminAnnotate(StatesGroup):
    # Short flow triggered by the "Add note" moderation button:
    # admin types free text that gets attached to the pending note.
    waiting_for_text = State()
