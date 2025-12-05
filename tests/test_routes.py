import pytest

# ----------------------------------------------------------------------
# Fixture factory for creating a book
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# CRUD tests
# ----------------------------------------------------------------------
async def test_create_book(async_client, book_data, create_book):
    book_id, data = await create_book(book_data)
    assert data["id"] == book_id
    assert data["title"] == book_data.title
    assert data["author"] == book_data.author
    assert data["year"] == book_data.year


async def test_get_books(async_client):
    resp = await async_client.get("/books/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_book(async_client, book_data, create_book):
    book_id, created = await create_book(book_data)
    resp = await async_client.get(f"/books/{book_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == book_id
    assert data["title"] == created["title"]
    assert data["author"] == created["author"]
    assert data["year"] == created["year"]


async def test_update_book(async_client, book_data, create_book):
    book_id, _ = await create_book(book_data)
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


async def test_delete_book(async_client, book_data, create_book):
    book_id, _ = await create_book(book_data)
    resp = await async_client.delete(f"/books/{book_id}")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Book deleted"

    resp = await async_client.get(f"/books/{book_id}")
    assert resp.status_code == 404
