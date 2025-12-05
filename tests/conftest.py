import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.db.models import Base, Book
from app.db.repository import BookRepository, get_session
from app.main import app

# ------------------------------------------------------------------------------
# Event loop для async-тестов
# ------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ------------------------------------------------------------------------------
# Клиенты для тестов
# ------------------------------------------------------------------------------
@pytest.fixture
def client():
    """Синхронный клиент FastAPI"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Асинхронный клиент FastAPI без базы"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# ------------------------------------------------------------------------------
# Моки для базы данных и сессий
# ------------------------------------------------------------------------------
@pytest.fixture
def mock_session():
    """Мок AsyncSession с заглушками для get/get_all"""
    session = AsyncMock()
    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()

    session.get_all_result = [
        {"id": 1, "title": "Mock Book", "author": "John", "pages": 100}
    ]
    session.get_result = {
        "id": 1, "title": "Mock Book", "author": "John", "pages": 100,
    }

    return session

@pytest.fixture(autouse=True)
def override_get_session(mock_session):
    """Перекрытие get_session для FastAPI (все эндпоинты используют мок)"""
    async def _override():
        yield mock_session

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.clear()

# ------------------------------------------------------------------------------
# Мок репозитория с динамическим списком книг
# ------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_repo():
    """Мок BookRepository с внутренним списком книг"""
    books = []
    repo = MagicMock(spec=BookRepository)

    async def create(book: Book):
        books.append(book)
        return book

    async def get_all():
        return books

    async def get(book_id: int):
        for b in books:
            if b.id == book_id:
                return b
        return None

    async def update(book_id: int, book: Book):
        for i, b in enumerate(books):
            if b.id == book_id:
                books[i] = book
                return book
        return None

    async def delete(book_id: int):
        for i, b in enumerate(books):
            if b.id == book_id:
                books.pop(i)
                return None

    repo.create = AsyncMock(side_effect=create)
    repo.get_all = AsyncMock(side_effect=get_all)
    repo.get = AsyncMock(side_effect=get)
    repo.update = AsyncMock(side_effect=update)
    repo.delete = AsyncMock(side_effect=delete)

    BookRepository.__new__ = lambda cls, session: repo
    yield

# ------------------------------------------------------------------------------
# Фикстуры с тестовыми данными
# ------------------------------------------------------------------------------
@pytest.fixture
def book_data():
    """Возвращает объект Book для тестов"""
    return Book(
        id=1,
        title="Test Book",
        author="John Doe",
        year=2026
    )

@pytest.fixture
def sample_books():
    """Фикстура с тестовыми книгами (ORM объекты)"""
    return [
        Book(id=1, title="Интеграция", author="Автор 1", year=2025),
        Book(id=2, title="Вторая книга", author="Автор 2", year=2024),
        Book(id=3, title="Старая книга", author="Автор 3", year=2023),
        Book(id=4, title="Для удаления", author="Автор 4", year=2022),
    ]

# ------------------------------------------------------------------------------
# In-memory SQLite база для интеграционных тестов
# ------------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    async_session = sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        await session.execute(text("DELETE FROM books"))
        await session.commit()
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def repository(db_session):
    return BookRepository(db_session)

@pytest_asyncio.fixture
async def override_get_db(db_session):
    """Подмена зависимости FastAPI get_session для интеграционных тестов"""
    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def async_client_with_db(override_get_db):
    """Асинхронный клиент FastAPI с реальной DB"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def created_book(async_client_with_db):
    """Фикстура для создания книги через эндпоинт"""
    async def _create(book_obj):
        if hasattr(book_obj, "model_dump"):
            payload = book_obj.model_dump()
        elif hasattr(book_obj, "__dict__"):
            payload = {k: v for k, v in vars(book_obj).items() if k in ("title", "author", "year")}
        else:
            payload = book_obj

        resp = await async_client_with_db.post("/books/", json=payload)
        assert resp.status_code == 200, f"Create book failed: {resp.text}"
        data = resp.json()
        return data["id"], data

    return _create
