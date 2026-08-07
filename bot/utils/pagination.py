"""
Small helpers shared by the "all notes" browsing handlers, e.g.
turning a note id + direction into the next note to fetch, or clamping
at the first/last approved note. Keep pagination math out of handlers.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Note
from bot.database.repositories.note_repo import (
    get_adjacent_approved,
    get_first_approved,
    get_last_approved,
)


async def get_first_approved_note(session: AsyncSession) -> Note | None:
    return await get_first_approved(session)


async def get_adjacent_approved_note(
    session: AsyncSession, current_id: int, direction: str
) -> Note | None:
    if direction not in {"next", "prev"}:
        raise ValueError("direction must be 'next' or 'prev'")
    return await get_adjacent_approved(session, current_id, direction, loop=True)
