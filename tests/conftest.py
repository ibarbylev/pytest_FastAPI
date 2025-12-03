import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from unittest.mock import AsyncMock, MagicMock
from app.db.repository import BookRepository, get_session
from app.db.models import Book
from app.main import app

# ------------------------------------------------------------------------------
# Клиенты для тестов
# ------------------------------------------------------------------------------

@pytest.fixture
def client():
    """
    Синхронный клиент FastAPI для тестов.
    Используется для обычных GET/POST запросов без async.
    """
    return TestClient(app)


@pytest.fixture
async def async_client():
    """
    Асинхронный клиент FastAPI для тестов.
    Используется для async-эндпоинтов.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# ------------------------------------------------------------------------------
# Моки для базы данных и сессий
# ------------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    """
    Мок AsyncSession для тестов.
    Здесь можно мокировать методы add, commit, refresh, delete и execute.
    Дополнительно задаются фиктивные результаты для get/get_all.
    """
    session = AsyncMock()
    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()

    # Заглушки для GET-запросов
    session.get_all_result = [
        {"id": 1, "title": "Mock Book", "author": "John", "pages": 100}
    ]
    session.get_result = {
        "id": 1,
        "title": "Mock Book",
        "author": "John",
        "pages": 100,
    }

    return session

@pytest.fixture(autouse=True)
def override_get_session(mock_session):
    """
    Перекрытие зависимости get_session для FastAPI.
    Все эндпоинты будут использовать mock_session вместо реальной базы.
    """
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
    """
    Мок BookRepository для тестов CRUD.
    Используется внутренний список books, который изменяется методами create/update/delete.
    Возвращаемые объекты — реальные Book, чтобы FastAPI корректно сериализовал их в JSON.
    """
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

    # Перехватываем конструктор BookRepository, чтобы возвращать мок
    BookRepository.__new__ = lambda cls, session: repo

    yield

# ------------------------------------------------------------------------------
# Фикстуры с тестовыми данными
# ------------------------------------------------------------------------------

@pytest.fixture
def book_data():
    """
    Возвращает объект Book для тестов.
    Используется во всех CRUD тестах как шаблон данных.
    """
    return Book(
        id=1,
        title="Test Book",
        author="John Doe",
        pages=123
    )
