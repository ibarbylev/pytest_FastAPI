import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.models import Base
from app.db.repository import BookRepository

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        connect_args={"check_same_thread": False}  # важно
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    async_session = sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        # очищаем таблицу перед тестом
        await session.execute(text("DELETE FROM books"))
        await session.commit()

        # --- проверка: вывести все id книг перед тестом ---
        result = await session.execute(text("SELECT id FROM books"))
        ids = [row[0] for row in result.fetchall()]
        print("Books before test:", ids)
        # -----------------------------------------------------

        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def repository(db_session):
    return BookRepository(db_session)  # Создаём репозиторий с сессией БД