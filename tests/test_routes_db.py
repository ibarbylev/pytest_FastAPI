import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.models import Book  # ORM модель


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
    """Фикстура с тестовыми данными для книг (ORM объекты)"""
    return [
        Book(id=1, title="Интеграция", author="Автор 1", year=2025),
        Book(id=2, title="Вторая книга", author="Автор 2", year=2024),
        Book(id=3, title="Старая книга", author="Автор 3", year=2023),
        Book(id=4, title="Для удаления", author="Автор 4", year=2022),
    ]


@pytest.fixture
async def created_book(async_client_with_db):
    """
    Фикстура для создания книги через эндпойнт.
    Возвращает функцию, которую можно вызвать с Book (ORM) или dict:
        book_id, data = await created_book(book_obj)
    """
    async def _create(book_obj):
        # Только нужные поля для POST (без id)
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


# ------------------------------------------------------------------------------
# CRUD tests
# ------------------------------------------------------------------------------

async def test_create_book(created_book, sample_books):
    """Тест создания книги"""
    book = sample_books[0]
    book_id, data = await created_book(book)

    assert data["id"] == book_id
    assert data["title"] == book.title
    assert data["author"] == book.author
    assert data["year"] == book.year


async def test_get_book(created_book, async_client_with_db, sample_books):
    """Тест получения книги по id"""
    book = sample_books[1]
    book_id, created = await created_book(book)

    resp = await async_client_with_db.get(f"/books/{book_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == book_id
    assert data["title"] == created["title"]
    assert data["author"] == created["author"]
    assert data["year"] == created["year"]


async def test_get_books(created_book, async_client_with_db, sample_books):
    """Тест получения списка книг"""
    # создаём все книги
    for book in sample_books:
        await created_book(book)

    resp = await async_client_with_db.get("/books/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= len(sample_books)  # проверяем, что созданные книги есть


async def test_update_book(created_book, async_client_with_db, sample_books):
    """Тест обновления книги"""
    book = sample_books[2]
    book_id, _ = await created_book(book)

    # В PUT обязательно передаём id
    updated_data = {
        "id": book_id,
        "title": "Новая книга",
        "author": "Автор 3 обновлён",
        "year": 2030
    }

    resp = await async_client_with_db.put(f"/books/{book_id}", json=updated_data)
    assert resp.status_code == 200, f"Update failed: {resp.text}"
    data = resp.json()

    assert data["id"] == book_id
    assert data["title"] == updated_data["title"]
    assert data["author"] == updated_data["author"]
    assert data["year"] == updated_data["year"]


async def test_delete_book(created_book, async_client_with_db, sample_books):
    """Тест удаления книги"""
    book = sample_books[3]
    book_id, _ = await created_book(book)

    resp = await async_client_with_db.delete(f"/books/{book_id}")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Book deleted"

    # Проверяем, что книги больше нет
    resp = await async_client_with_db.get(f"/books/{book_id}")
    assert resp.status_code == 404
