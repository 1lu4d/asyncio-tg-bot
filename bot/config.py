"""
Application configuration, loaded from environment variables / .env.
Uses pydantic-settings so required values are validated at startup
instead of failing deep inside a handler at 2am.
"""
from typing import Annotated

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Explicit load_dotenv() call as a workaround: on Python 3.14,
# pydantic-settings (>=2.13) can silently skip its own env_file loading
# unless a debugger is attached (see pydantic/pydantic-settings#795).
# Loading it into os.environ ourselves sidesteps that bug entirely.
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    admin_ids: Annotated[list[int], NoDecode]
    announcement_channel: str | None = None
    db_path: str = "data/dictionary.db"
    # How many seconds a sent random-note message is considered "fresh"
    # and may be edited instead of deleted+resent. Can be overridden in .env
    recent_random_message_seconds: int = 120

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: str | list[int]) -> list[int]:
        # Lets ADMIN_IDS be a plain comma-separated string in .env,
        # e.g. ADMIN_IDS=111111111,222222222
        if isinstance(value, str):
            return [int(x.strip()) for x in value.split(",") if x.strip()]
        return value

    @property
    def db_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path}"


settings = Settings()
