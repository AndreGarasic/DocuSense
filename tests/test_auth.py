"""
Tests for JWT Authentication endpoints.
"""
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def test_client():
    """Create test client."""
    return AsyncClient(app=app, base_url="http://test")


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self, test_client):
        """Test successful login returns JWT token."""
        async with test_client as client:
            response = await client.post(
                "/api/v1/auth/token",
                data={"username": "admin", "password": "admin123"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, test_client):
        """Test login with invalid credentials returns 401."""
        async with test_client as client:
            response = await client.post(
                "/api/v1/auth/token",
                data={"username": "admin", "password": "wrongpassword"},
            )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, test_client):
        """Test login with nonexistent user returns 401."""
        async with test_client as client:
            response = await client.post(
                "/api/v1/auth/token",
                data={"username": "nonexistent", "password": "password"},
            )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, test_client):
        """Test getting current user with valid token."""
        async with test_client as client:
            # First login to get token
            login_response = await client.post(
                "/api/v1/auth/token",
                data={"username": "user", "password": "user123"},
            )
            token = login_response.json()["access_token"]
            
            # Use token to get current user
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "user"
        assert data["role"] == "user"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, test_client):
        """Test getting current user without token returns 401."""
        async with test_client as client:
            response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, test_client):
        """Test getting current user with invalid token returns 401."""
        async with test_client as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid_token"},
            )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_token(self, test_client):
        """Test token verification endpoint."""
        async with test_client as client:
            # First login to get token
            login_response = await client.post(
                "/api/v1/auth/token",
                data={"username": "admin", "password": "admin123"},
            )
            token = login_response.json()["access_token"]
            
            # Verify token
            response = await client.get(
                "/api/v1/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["username"] == "admin"


class TestProtectedEndpoints:
    """Test protected endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_clear_cache_requires_auth(self, test_client):
        """Test cache clear endpoint requires authentication."""
        async with test_client as client:
            response = await client.delete("/api/v1/ask/cache")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_clear_cache_requires_admin(self, test_client):
        """Test cache clear endpoint requires admin role."""
        async with test_client as client:
            # Login as regular user
            login_response = await client.post(
                "/api/v1/auth/token",
                data={"username": "user", "password": "user123"},
            )
            token = login_response.json()["access_token"]
            
            # Try to clear cache
            response = await client.delete(
                "/api/v1/ask/cache",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 403
        assert "Admin role required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_clear_cache_admin_success(self, test_client):
        """Test admin can clear cache."""
        async with test_client as client:
            # Login as admin
            login_response = await client.post(
                "/api/v1/auth/token",
                data={"username": "admin", "password": "admin123"},
            )
            token = login_response.json()["access_token"]
            
            # Clear cache
            response = await client.delete(
                "/api/v1/ask/cache",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "Cache cleared successfully" in data["message"]
        assert data["cleared_by"] == "admin"
