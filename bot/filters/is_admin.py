"""
Restricts a router (or a single handler) to configured admins.
Usage: router.message.filter(IsAdmin())
"""
from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from bot.config import settings


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and user.id in settings.admin_ids)
