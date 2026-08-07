"""
Data-access methods for User.

Keep raw SQLAlchemy queries out of handlers - handlers call these
functions, they don't call `session.execute(...)` directly. Makes it
much easier to test business logic and to swap storage later.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from bot.database.models import User
from bot.config import settings


async def get_or_create(session: AsyncSession, tg_id: int, username: str | None) -> User:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(tg_id=tg_id, username=username)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise
    else:
        await session.refresh(user)   # loads the auto-generated id back onto the object
    return user


async def is_admin(session: AsyncSession, tg_id: int) -> bool:
    return tg_id in settings.admin_ids
