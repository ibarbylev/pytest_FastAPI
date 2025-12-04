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
        year=2026
    )

# ------------------------------------------------------------------------------
# Фикстуры для test_repository_db
# ------------------------------------------------------------------------------

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.models import Base


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



# ------------------------------------------------------------------------------
# Фикстуры для test_routes_db.py
# ------------------------------------------------------------------------------



import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.db.repository import get_session
from app.main import app

# SQLite in-memory для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine():
    """
    Создаёт in-memory SQLite движок и создаёт все таблицы.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """
    Асинхронная сессия SQLAlchemy для интеграционных тестов.
    """
    async_session = sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def override_get_db(db_session):
    """
    Подмена зависимости FastAPI get_session, чтобы использовать тестовую базу.
    """
    from app.main import app
    from app.db.repository import get_session

    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client_with_db(override_get_db):
    """
    Асинхронный клиент FastAPI для интеграционных тестов с реальной DB.
    Использует ASGITransport для работы без реального HTTP сервера.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    import pytest
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    # ------------------------------------------------------------------------------
    # fixtures
    # ------------------------------------------------------------------------------

    @pytest.fixture
    async def async_client_with_db(override_get_db):
        """Асинхронный клиент FastAPI для интеграционных тестов с реальной DB."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def sample_books():
        """Фикстура с тестовыми данными для книг"""
        return [
            {"id": 1, "title": "Интеграция", "author": "Тест Автор", "year": 2025},
            {"id": 2, "title": "Вторая книга", "author": "Автор 2", "year": 2024},
            {"id": 3, "title": "Старая книга", "author": "Автор 3", "year": 2023},
            {"id": 4, "title": "Для удаления", "author": "Автор 4", "year": 2022},
        ]

    @pytest.fixture
    async def created_book(async_client_with_db):
        """
        Фикстура для создания книги и возврата (id, data).
        Можно параметризовать в тестах, чтобы создавать разные книги.
        """

        async def _create(book_data: dict):
            resp = await async_client_with_db.post("/books/", json=book_data)
            assert resp.status_code == 200
            data = resp.json()
            return data["id"], data

        return _create
