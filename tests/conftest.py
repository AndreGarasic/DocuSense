"""
DocuSense - Test Configuration and Fixtures
"""
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# Alias for backward compatibility
@pytest.fixture
def sample_item():
    """Sample item data for testing."""
    return {
        "name": "Test Item",
        "description": "A test item description",
        "price": 29.99,
        "is_active": True,
    }


@pytest.fixture
def sample_item_update():
    """Sample item update data for testing."""
    return {
        "name": "Updated Item",
        "price": 39.99,
    }
