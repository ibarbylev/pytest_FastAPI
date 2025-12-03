import pytest

### Тест создания книги (POST `/books/`)

@pytest.mark.asyncio
async def test_create_book(async_client):
    book_data = {
        "id": 1,
        "title": "Test Book",
        "author": "John Doe",
        "pages": 123
    }
    response = await async_client.post("/books/", json=book_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["author"] == "John Doe"


### Тест получения всех книг (GET `/books/`)

@pytest.mark.asyncio
async def test_get_books(async_client):
    response = await async_client.get("/books/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


### Тест получения книги по ID (GET `/books/{book_id}`)

@pytest.mark.asyncio
async def test_get_book(async_client):
    book_id = 1
    response = await async_client.get(f"/books/{book_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id


### Тест обновления книги (PUT `/books/{book_id}`)

@pytest.mark.asyncio
async def test_update_book(async_client):
    book_id = 1
    updated_data = {
        "id": book_id,
        "title": "Updated Book",
        "author": "Jane Doe",
        "pages": 321
    }
    response = await async_client.put(f"/books/{book_id}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Book"


### Тест удаления книги (DELETE `/books/{book_id}`)

@pytest.mark.asyncio
async def test_delete_book(async_client):
    book_id = 1
    response = await async_client.delete(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Book deleted"