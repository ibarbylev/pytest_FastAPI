import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


async def async_client_with_db(override_get_db):
    """
    Асинхронный клиент FastAPI для интеграционных тестов с реальной DB.
    Использует ASGITransport для работы без реального HTTP сервера.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_create_book(async_client_with_db):
    book_data = {
        "id": 1,
        "title": "Интеграция",
        "author": "Тест Автор",
        "year": 2025
    }

    response = await async_client_with_db.post("/books/", json=book_data)
    assert response.status_code == 200

    data = response.json()
    assert data == book_data


async def test_get_book(async_client_with_db):
    # создаём книгу
    book_data = {
        "id": 2,
        "title": "Вторая книга",
        "author": "Автор 2",
        "year": 2024
    }
    await async_client_with_db.post("/books/", json=book_data)

    # получаем по ID
    response = await async_client_with_db.get("/books/2")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Вторая книга"


async def test_update_book(async_client_with_db):
    # создаём книгу
    book_data = {
        "id": 3,
        "title": "Старая книга",
        "author": "Автор 3",
        "year": 2023
    }
    await async_client_with_db.post("/books/", json=book_data)

    updated_data = {
        "id": 3,
        "title": "Новая книга",
        "author": "Автор 3 обновлён",
        "year": 2030
    }

    response = await async_client_with_db.put("/books/3", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data == updated_data


async def test_delete_book(async_client_with_db):
    # создаём книгу
    book_data = {
        "id": 4,
        "title": "Для удаления",
        "author": "Автор 4",
        "year": 2022
    }
    await async_client_with_db.post("/books/", json=book_data)

    # удаляем
    response = await async_client_with_db.delete("/books/4")
    assert response.status_code == 200
    assert response.json()["message"] == "Book deleted"

    # проверяем, что книги больше нет
    response = await async_client_with_db.get("/books/4")
    assert response.status_code == 404
