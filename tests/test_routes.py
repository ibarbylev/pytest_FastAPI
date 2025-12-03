import pytest

### Тест создания книги (POST `/books/`)

@pytest.mark.asyncio
async def test_create_book(async_client, book_data):
    response = await async_client.post("/books/", json=book_data.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == book_data.title


### Тест получения всех книг (GET `/books/`)

@pytest.mark.asyncio
async def test_get_books(async_client):
    response = await async_client.get("/books/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


### Тест получения книги по ID (GET `/books/{book_id}`)

@pytest.mark.asyncio
async def test_get_book(async_client, book_data):
    # Сначала создаём книгу
    create_resp = await async_client.post("/books/", json=book_data.model_dump())
    assert create_resp.status_code == 200

    # Теперь можно получить её
    book_id = book_data.id
    response = await async_client.get(f"/books/{book_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id
    assert data["title"] == book_data.title



### Тест обновления книги (PUT `/books/{book_id}`)

@pytest.mark.asyncio
async def test_update_book(async_client, book_data):
    # Сначала создаём книгу
    create_resp = await async_client.post("/books/", json=book_data.model_dump())
    assert create_resp.status_code == 200

    # Данные для обновления
    updated_data = {
        "id": book_data.id,
        "title": "Updated Book",
        "author": "Jane Doe",
        "pages": 321
    }

    # Обновляем книгу
    response = await async_client.put(f"/books/{book_data.id}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Book"
    assert data["author"] == "Jane Doe"



### Тест удаления книги (DELETE `/books/{book_id}`)

@pytest.mark.asyncio
async def test_delete_book(async_client):
    book_id = 1
    response = await async_client.delete(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Book deleted"