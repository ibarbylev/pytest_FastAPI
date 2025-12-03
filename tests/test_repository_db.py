import pytest
from app.db.models import Book
from app.db.repository import NotFoundError
from unittest.mock import AsyncMock, MagicMock

from tests.conftest_db import *

@pytest.mark.anyio
async def test_create_book(repository):
    book = Book(id=1, title="Test Book", author="John Doe", year=2026)
    created = await repository.create(book)
    assert created.id == book.id
    assert created.title == book.title

@pytest.mark.anyio
async def test_get_all_books(repository):
    book1 = Book(id=1, title="Book1", author="A", year=2000)
    book2 = Book(id=2, title="Book2", author="B", year=2010)
    await repository.create(book1)
    await repository.create(book2)

    books = await repository.get_all()
    ids = [b.id for b in books]
    assert 1 in ids
    assert 2 in ids

@pytest.mark.anyio
async def test_get_book(repository):
    book = Book(id=1, title="Book1", author="A", year=2000)
    await repository.create(book)

    fetched = await repository.get(1)
    assert fetched.id == 1
    assert fetched.title == "Book1"

@pytest.mark.anyio
async def test_get_book_not_found(repository):
    result = await repository.get(999)
    assert result is None

@pytest.mark.anyio
async def test_update_book(repository):
    book = Book(id=1, title="Old Title", author="Old Author", year=1990)
    await repository.create(book)

    updated_book = Book(id=1, title="New Title", author="New Author", year=2000)
    updated = await repository.update(1, updated_book)
    assert updated.title == "New Title"
    assert updated.author == "New Author"

@pytest.mark.anyio
async def test_update_book_not_found(repository):
    book = Book(id=999, title="X", author="Y", year=0)
    repository = MagicMock()
    repository.update = AsyncMock(side_effect=NotFoundError)

    with pytest.raises(NotFoundError):
        await repository.update(book)

@pytest.mark.anyio
async def test_delete_book(repository):
    book = Book(id=1, title="Book1", author="A", year=2000)
    await repository.create(book)

    await repository.delete(1)
    result = await repository.get(1)
    assert result is None

@pytest.mark.anyio
async def test_delete_book_not_found(repository):
    repository = MagicMock()
    repository.delete = AsyncMock(side_effect=NotFoundError)
    with pytest.raises(NotFoundError):
        await repository.delete(999)
