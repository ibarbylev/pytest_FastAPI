# tests/test_routes.py

import pytest

# ------------------------------------------------------------------------------
# Тесты CRUD для эндпойнтов /books/
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_book(async_client, book_data):
    """
    Тест создания книги через POST `/books/`.

    Используется фикстура book_data как шаблон книги.
    Проверяет, что эндпойнт возвращает корректный объект Book.
    """
    response = await async_client.post("/books/", json=book_data.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == book_data.title
    assert data["author"] == book_data.author
    assert data["year"] == book_data.year


@pytest.mark.asyncio
async def test_get_books(async_client):
    """
    Тест получения всех книг через GET `/books/`.

    Проверяет, что эндпойнт возвращает список объектов.
    """
    response = await async_client.get("/books/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_book(async_client, book_data):
    """
    Тест получения книги по ID через GET `/books/{book_id}`.

    Сначала создаёт книгу через POST `/books/`, затем получает её по ID.
    Проверяет корректность возвращаемого объекта.
    """
    create_resp = await async_client.post("/books/", json=book_data.model_dump())
    assert create_resp.status_code == 200

    book_id = book_data.id
    response = await async_client.get(f"/books/{book_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id
    assert data["title"] == book_data.title
    assert data["author"] == book_data.author
    assert data["year"] == book_data.year


@pytest.mark.asyncio
async def test_update_book(async_client, book_data):
    """
    Тест обновления книги через PUT `/books/{book_id}`.

    Сначала создаёт книгу, затем обновляет поля title, author и year.
    Проверяет, что эндпойнт возвращает обновлённый объект.
    """
    create_resp = await async_client.post("/books/", json=book_data.model_dump())
    assert create_resp.status_code == 200

    updated_data = {
        "id": book_data.id,
        "title": "Updated Book",
        "author": "Jane Doe",
        "year": 2000
    }

    response = await async_client.put(f"/books/{book_data.id}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Book"
    assert data["author"] == "Jane Doe"
    assert data["year"] == 2000


@pytest.mark.asyncio
async def test_delete_book(async_client, book_data):
    """
    Тест удаления книги через DELETE `/books/{book_id}`.

    Сначала создаёт книгу, затем удаляет её.
    Проверяет, что эндпойнт возвращает сообщение об удалении.
    Проверяет, что книга больше не существует.
    """
    create_resp = await async_client.post("/books/", json=book_data.model_dump())
    assert create_resp.status_code == 200

    book_id = book_data.id
    response = await async_client.delete(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Book deleted"

    get_resp = await async_client.get(f"/books/{book_id}")
    assert get_resp.status_code == 404
    data = get_resp.json()
    assert data is None or data ==  {'detail': 'Book with id=1 not found'}
