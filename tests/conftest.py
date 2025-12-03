# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.main import app


@pytest.fixture
def client():
    """Синхронный клиент для тестов"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Асинхронный клиент для тестов"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_example(async_client):
    response = await async_client.get("/books/")
    assert response.status_code == 200