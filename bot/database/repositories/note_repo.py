"""
Data-access methods for Note (submission, moderation, browsing).
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from datetime import datetime, timezone

from bot.database.models import Note, NoteStatus


async def create_pending(
    session: AsyncSession, author_id: int, file_id: str, caption: str | None
) -> Note:
    note = Note(author_id=author_id, file_id=file_id, caption=caption, status=NoteStatus.PENDING)
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note

async def set_status(
    session: AsyncSession, note_id: int, status: NoteStatus, moderator_id: int
) -> None:
    note = await session.get(Note, note_id)   # simpler than select() when looking up by primary key
    if note is None: return
    note.status = status
    note.moderated_by = moderator_id
    note.moderated_at = datetime.now(timezone.utc)
    await session.commit()


async def add_admin_note(session: AsyncSession, note_id: int, text: str) -> None:
    # Update admin_note field
    note = await session.get(Note, note_id)
    if note is None: return
    note.admin_note = text
    await session.commit()


async def get_random_approved(session: AsyncSession) -> Note | None:
    result = await session.execute(
        select(Note).where(Note.status == NoteStatus.APPROVED).order_by(func.random()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_random_approved_excluding(
    session: AsyncSession, exclude_ids: list[int] | None = None
) -> Note | None:
    query = select(Note).where(Note.status == NoteStatus.APPROVED)
    if exclude_ids:
        query = query.where(Note.id.not_in(exclude_ids))

    result = await session.execute(query.order_by(func.random()).limit(1))
    note = result.scalar_one_or_none()
    if note is not None:
        return note

    if exclude_ids:
        result = await session.execute(
            select(Note).where(Note.status == NoteStatus.APPROVED).order_by(func.random()).limit(1)
        )
        return result.scalar_one_or_none()

    return None


async def count_approved(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count()).select_from(Note).where(Note.status == NoteStatus.APPROVED)
    )
    return result.scalar_one()


async def get_approved_note_position(session: AsyncSession, note_id: int) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Note)
        .where(Note.status == NoteStatus.APPROVED, Note.id <= note_id)
    )
    return result.scalar_one()


async def get_first_approved(session: AsyncSession) -> Note | None:
    result = await session.execute(
        select(Note).where(Note.status == NoteStatus.APPROVED).order_by(Note.id.asc()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_last_approved(session: AsyncSession) -> Note | None:
    result = await session.execute(
        select(Note).where(Note.status == NoteStatus.APPROVED).order_by(Note.id.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_adjacent_approved(
    session: AsyncSession,
    current_id: int,
    direction: str,
    loop: bool = False,
) -> Note | None:
    query = select(Note).where(Note.status == NoteStatus.APPROVED)
    if direction == "next":
        query = query.where(Note.id > current_id).order_by(Note.id.asc())
    else:
        query = query.where(Note.id < current_id).order_by(Note.id.desc())

    result = await session.execute(query.limit(1))
    note = result.scalar_one_or_none()
    if note is None and loop:
        return await get_first_approved(session) if direction == "next" else await get_last_approved(session)
    return note
