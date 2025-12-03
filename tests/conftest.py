# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    """Not awaitable client for tests"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Awaitable client for tests"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


from unittest.mock import AsyncMock

@pytest.fixture
def mock_session():
    session = AsyncMock()
    # Репозиторий будет ожидать методы add, commit, refresh, delete
    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()

    # --- Данные для mock get_all ---
    session.get_all_result = [
        {"id": 1, "title": "Mock Book", "author": "John", "pages": 100}
    ]

    # --- Данные для mock get ---
    session.get_result = {
        "id": 1,
        "title": "Mock Book",
        "author": "John",
        "pages": 100,
    }

    return session

#### Перекрываем зависимость get_session

from app.db.repository import get_session

@pytest.fixture(autouse=True)
def override_get_session(mock_session):
    async def _override():
        yield mock_session
    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.clear()


from unittest.mock import AsyncMock, MagicMock
from app.db.repository import BookRepository
from app.db.models import Book

@pytest.fixture(autouse=True)
def mock_repo():
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

    # Важный момент: не MagicMock, а реальные Book объекты
    BookRepository.__new__ = lambda cls, session: repo

    yield



@pytest.fixture
def book_data():
    """Возвращает Pydantic/SQLAlchemy объект Book для тестов"""
    return Book(
        id=1,
        title="Test Book",
        author="John Doe",
        pages=123
    )