"""
Data-access methods for Reaction.

Business rule (enforced here, not in handlers): one reaction per user
per note. Pressing the same reaction again removes it (toggle off);
pressing a different one replaces the old one.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import Reaction
from sqlalchemy import func, select


async def set_reaction(session: AsyncSession, note_id: int, user_id: int, reaction: str) -> None:
    # Look up existing Reaction(note_id, user_id):
    #   - none        -> insert
    #   - same value   -> delete (toggle off)
    #   - different    -> update value
    result = await session.execute(
    select(Reaction).where(Reaction.note_id == note_id, Reaction.user_id == user_id)
    )
    existing = result.scalar_one_or_none()
    if existing is None:
        reaction = Reaction(note_id=note_id, user_id=user_id, reaction=reaction)
        session.add(reaction)
        await session.commit()
        await session.refresh(reaction)
    elif existing.reaction == reaction:
        await session.delete(existing)
        await session.commit()
    else:
        existing.reaction = reaction
        await session.commit()
        await session.refresh(existing)


async def get_counts(session: AsyncSession, note_id: int) -> dict[str, int]:
    result = await session.execute(
        select(Reaction.reaction, func.count())
        .where(Reaction.note_id == note_id)
        .group_by(Reaction.reaction)
    )
    return dict(result.all())