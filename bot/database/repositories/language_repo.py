"""
Language preference storage helper.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.database.models import User


async def get_user_language(session: AsyncSession, tg_id: int) -> str | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    return getattr(user, "language", None)


async def set_user_language(session: AsyncSession, tg_id: int, language: str) -> None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user is None:
        return
    setattr(user, "language", language)
    await session.commit()
