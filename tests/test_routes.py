import pytest

# ------------------------------------------------------------------------------
# helper (вспомогательная функция)
# ------------------------------------------------------------------------------


async def create_book(async_client, book_data):
    """Хелпер для создания книги и возврата (id, json-объект)."""
    resp = await async_client.post("/books/", json=book_data.model_dump())
    assert resp.status_code == 200
    data = resp.json()
    return data["id"], data


# ------------------------------------------------------------------------------
# CRUD tests for /books/
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_book(async_client, book_data):
    """Тест создания книги"""
    book_id, data = await create_book(async_client, book_data)

    assert data["title"] == book_data.title
    assert data["author"] == book_data.author
    assert data["year"] == book_data.year
    assert data["id"] == book_id


@pytest.mark.asyncio
async def test_get_books(async_client):
    """Тест получения списка книг"""
    resp = await async_client.get("/books/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_book(async_client, book_data):
    """Тест получения книги по `id`"""
    book_id, created = await create_book(async_client, book_data)

    resp = await async_client.get(f"/books/{book_id}")
    assert resp.status_code == 200

    data = resp.json()
    assert data["id"] == book_id
    assert data["title"] == created["title"]
    assert data["author"] == created["author"]
    assert data["year"] == created["year"]


@pytest.mark.asyncio
async def test_update_book(async_client, book_data):
    """Тест изменения книги по `id`"""
    book_id, _ = await create_book(async_client, book_data)

    updated = {
        "id": book_id,
        "title": "Updated Book",
        "author": "Jane Doe",
        "year": 2000,
    }

    resp = await async_client.put(f"/books/{book_id}", json=updated)
    assert resp.status_code == 200

    data = resp.json()
    assert data == updated


@pytest.mark.asyncio
async def test_delete_book(async_client, book_data):
    """Тест удаления книги по `id`"""
    book_id, _ = await create_book(async_client, book_data)

    resp = await async_client.delete(f"/books/{book_id}")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Book deleted"

    # Проверяем, что книга реально исчезла
    resp = await async_client.get(f"/books/{book_id}")
    assert resp.status_code == 404
    assert resp.json().get("detail")
