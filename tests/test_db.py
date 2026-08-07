import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from bot.database.models import Base, Note, NoteStatus, User
from bot.database.repositories.language_repo import get_user_language, set_user_language
from bot.database.repositories.note_repo import (
    count_approved,
    get_approved_note_position,
)
from bot.database.repositories.user_repo import get_or_create


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(async_engine):
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    async with async_session() as db:
        yield db


@pytest.mark.asyncio
async def test_get_or_create_user_creates_and_returns_same_user(session):
    user = await get_or_create(session, 12345, "tester")
    assert user.tg_id == 12345
    assert user.username == "tester"

    same_user = await get_or_create(session, 12345, "tester")
    assert same_user.id == user.id
    assert same_user.username == "tester"


@pytest.mark.asyncio
async def test_user_language_defaults_to_english_and_can_be_updated(session):
    await get_or_create(session, 23456, "languser")
    assert await get_user_language(session, 23456) == "en"

    await set_user_language(session, 23456, "ru")
    assert await get_user_language(session, 23456) == "ru"


@pytest.mark.asyncio
async def test_note_position_and_count_approved(session):
    user = User(tg_id=34567, username="noteuser")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    approved_notes = [
        Note(author_id=user.id, file_id="file1", caption="one", status=NoteStatus.APPROVED),
        Note(author_id=user.id, file_id="file2", caption="two", status=NoteStatus.APPROVED),
        Note(author_id=user.id, file_id="file3", caption="three", status=NoteStatus.APPROVED),
    ]
    session.add_all(approved_notes)
    await session.commit()

    assert await count_approved(session) == 3
    assert await get_approved_note_position(session, approved_notes[0].id) == 1
    assert await get_approved_note_position(session, approved_notes[1].id) == 2
    assert await get_approved_note_position(session, approved_notes[2].id) == 3
