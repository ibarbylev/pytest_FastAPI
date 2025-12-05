import pytest

# ----------------------------------------------------------------------
# CRUD tests с реальной базой
# ----------------------------------------------------------------------
async def test_create_book(created_book, sample_books):
    book = sample_books[0]
    book_id, data = await created_book(book)
    assert data["id"] == book_id
    assert data["title"] == book.title
    assert data["author"] == book.author
    assert data["year"] == book.year


async def test_get_book(created_book, async_client_with_db, sample_books):
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
    for book in sample_books:
        await created_book(book)
    resp = await async_client_with_db.get("/books/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= len(sample_books)


async def test_update_book(created_book, async_client_with_db, sample_books):
    book = sample_books[2]
    book_id, _ = await created_book(book)
    updated_data = {
        "id": book_id,
        "title": "Новая книга",
        "author": "Автор 3 обновлён",
        "year": 2030
    }
    resp = await async_client_with_db.put(f"/books/{book_id}", json=updated_data)
    assert resp.status_code == 200
    data = resp.json()
    assert data == updated_data


async def test_delete_book(created_book, async_client_with_db, sample_books):
    book = sample_books[3]
    book_id, _ = await created_book(book)
    resp = await async_client_with_db.delete(f"/books/{book_id}")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Book deleted"

    resp = await async_client_with_db.get(f"/books/{book_id}")
    assert resp.status_code == 404
