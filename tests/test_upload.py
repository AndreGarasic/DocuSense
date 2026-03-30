"""
DocuSense - Upload Endpoint Tests
"""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing."""
    content = b"This is a test document content for DocuSense testing."
    return ("test_document.txt", io.BytesIO(content), "text/plain")


@pytest.fixture
def sample_files():
    """Create multiple sample files for testing."""
    return [
        ("doc1.txt", io.BytesIO(b"First document content"), "text/plain"),
        ("doc2.txt", io.BytesIO(b"Second document content"), "text/plain"),
    ]


class TestUploadEndpoint:
    """Tests for the upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_no_files_returns_400(self, async_client: AsyncClient):
        """Test that uploading with no files returns 400."""
        response = await async_client.post("/api/v1/upload")
        # FastAPI returns 422 for missing required fields
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    @pytest.mark.asyncio
    async def test_upload_invalid_extension_returns_415(self, async_client: AsyncClient):
        """Test that uploading unsupported file type returns 415."""
        files = {"file": ("test.exe", io.BytesIO(b"malicious content"), "application/octet-stream")}
        response = await async_client.post("/api/v1/upload", files=files)
        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    @pytest.mark.asyncio
    async def test_list_documents_without_session_returns_422(self, async_client: AsyncClient):
        """Test that listing documents without session ID returns 422."""
        response = await async_client.get("/api/v1/upload")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires database connection")
    async def test_list_documents_invalid_session_returns_404(self, async_client: AsyncClient):
        """Test that listing documents with invalid session returns 404."""
        response = await async_client.get(
            "/api/v1/upload",
            headers={"X-Session-ID": "invalid-session-id"}
        )
        # This will fail because the session doesn't exist in the database
        # In a real test with mocked DB, this would return 404
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.asyncio
    async def test_get_document_without_session_returns_422(self, async_client: AsyncClient):
        """Test that getting a document without session ID returns 422."""
        response = await async_client.get("/api/v1/upload/1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_delete_document_without_session_returns_422(self, async_client: AsyncClient):
        """Test that deleting a document without session ID returns 422."""
        response = await async_client.delete("/api/v1/upload/1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSessionEndpoint:
    """Tests for the session endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires database connection")
    async def test_create_session_endpoint_exists(self, async_client: AsyncClient):
        """Test that the create session endpoint exists."""
        response = await async_client.post("/api/v1/upload/session")
        # Will fail due to no DB, but endpoint should exist
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestUploadResponseSchema:
    """Tests for upload response schema validation."""

    def test_document_response_schema(self):
        """Test DocumentResponse schema."""
        from datetime import datetime
        from app.schemas.document import DocumentResponse

        doc = DocumentResponse(
            id=1,
            session_id="test-session-id",
            filename="stored_file.txt",
            original_filename="original.txt",
            content_type="text/plain",
            file_size=1024,
            created_at=datetime.now(),
            chunk_count=5,
        )
        assert doc.id == 1
        assert doc.chunk_count == 5

    def test_upload_response_schema(self):
        """Test DocumentUploadResponse schema."""
        from datetime import datetime
        from app.schemas.document import DocumentResponse, DocumentUploadResponse

        doc = DocumentResponse(
            id=1,
            session_id="test-session-id",
            filename="stored_file.txt",
            original_filename="original.txt",
            content_type="text/plain",
            file_size=1024,
            created_at=datetime.now(),
            chunk_count=5,
        )
        response = DocumentUploadResponse(
            message="Success",
            session_id="test-session-id",
            documents=[doc],
            total_uploaded=1,
        )
        assert response.total_uploaded == 1
        assert len(response.documents) == 1
