from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.database.models import AdminNotification


async def add_notification(
    session: AsyncSession, note_id: int, chat_id: int, message_id: int
) -> None:
    notification = AdminNotification(
        note_id=note_id,
        chat_id=chat_id,
        message_id=message_id,
        created_at=datetime.now(timezone.utc),
    )
    session.add(notification)
    await session.commit()


async def get_notifications_for_note(session: AsyncSession, note_id: int):
    result = await session.execute(
        select(AdminNotification).where(AdminNotification.note_id == note_id)
    )
    return result.scalars().all()


async def delete_notifications_for_note(session: AsyncSession, note_id: int):
    notifications = await get_notifications_for_note(session, note_id)
    for notification in notifications:
        await session.delete(notification)
    await session.commit()
    return notifications