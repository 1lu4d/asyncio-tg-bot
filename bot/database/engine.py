"""
Async engine + session factory.

init_db() creates tables on startup via create_all - fine while you're
building (Phase 1-5 in the roadmap). Once the schema stabilizes and
you're about to deploy for real, switch to Alembic migrations instead
of create_all so future schema changes don't require wiping the DB.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.config import settings
from bot.database.models import Base

engine = create_async_engine(settings.db_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        if conn.dialect.name == "sqlite":
            result = await conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            if "language" not in columns:
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN language VARCHAR(8) DEFAULT 'en' NOT NULL")
                )
