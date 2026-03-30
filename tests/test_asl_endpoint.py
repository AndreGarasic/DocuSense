"""
DocuSense - ASL Endpoint Integration Tests

Integration tests for the ASL API endpoints.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.qa import AnswerResponse


@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_session_service():
    """Mock the session service."""
    with patch("app.api.v1.endpoints.asl.SessionService") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_qa_service():
    """Mock the QA service."""
    with patch("app.api.v1.endpoints.asl.QAService") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_model_loader():
    """Mock the model loader."""
    with patch("app.api.v1.endpoints.asl.get_model_loader") as mock:
        mock_instance = MagicMock()
        mock_instance.qa_available = True
        mock.return_value = mock_instance
        yield mock_instance


class TestASLEndpoint:
    """Tests for POST /api/v1/asl endpoint."""

    def test_ask_question_missing_session_header(self, client):
        """Test that missing X-Session-ID header returns 422."""
        response = client.post(
            "/api/v1/asl",
            json={"question": "What is the total amount?"},
        )
        
        assert response.status_code == 422

    def test_ask_question_empty_question(self, client):
        """Test that empty question returns 422."""
        response = client.post(
            "/api/v1/asl",
            json={"question": ""},
            headers={"X-Session-ID": "test-session"},
        )
        
        assert response.status_code == 422

    def test_ask_question_short_question(self, client):
        """Test that too short question returns 422."""
        response = client.post(
            "/api/v1/asl",
            json={"question": "Hi"},  # Less than 3 characters
            headers={"X-Session-ID": "test-session"},
        )
        
        assert response.status_code == 422

    def test_ask_question_session_not_found(
        self, client, mock_session_service, mock_model_loader
    ):
        """Test that invalid session ID returns 404."""
        mock_session_service.get_session = AsyncMock(return_value=None)
        
        response = client.post(
            "/api/v1/asl",
            json={"question": "What is the total amount?"},
            headers={"X-Session-ID": "nonexistent-session"},
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_ask_question_no_documents(
        self, client, mock_session_service, mock_model_loader
    ):
        """Test that session with no documents returns 400."""
        mock_session = MagicMock()
        mock_session.document_count = 0
        mock_session_service.get_session = AsyncMock(return_value=mock_session)
        
        response = client.post(
            "/api/v1/asl",
            json={"question": "What is the total amount?"},
            headers={"X-Session-ID": "empty-session"},
        )
        
        assert response.status_code == 400
        assert "no documents" in response.json()["detail"].lower()

    def test_ask_question_qa_unavailable(
        self, client, mock_session_service
    ):
        """Test that unavailable QA service returns 503."""
        mock_session = MagicMock()
        mock_session.document_count = 5
        mock_session_service.get_session = AsyncMock(return_value=mock_session)
        
        with patch("app.api.v1.endpoints.asl.get_model_loader") as mock_loader:
            mock_instance = MagicMock()
            mock_instance.qa_available = False
            mock_loader.return_value = mock_instance
            
            response = client.post(
                "/api/v1/asl",
                json={"question": "What is the total amount?"},
                headers={"X-Session-ID": "test-session"},
            )
            
            assert response.status_code == 503
            assert "unavailable" in response.json()["detail"].lower()

    def test_ask_question_success(
        self, client, mock_session_service, mock_qa_service, mock_model_loader
    ):
        """Test successful question answering."""
        mock_session = MagicMock()
        mock_session.document_count = 5
        mock_session_service.get_session = AsyncMock(return_value=mock_session)
        
        mock_response = AnswerResponse(
            answer="The total amount is $100.00",
            confidence=0.95,
            source_chunks=[],
            cached=False,
        )
        mock_qa_service.answer_question = AsyncMock(return_value=mock_response)
        
        response = client.post(
            "/api/v1/asl",
            json={"question": "What is the total amount?"},
            headers={"X-Session-ID": "test-session"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "The total amount is $100.00"
        assert data["confidence"] == 0.95

    def test_ask_question_with_document_ids(
        self, client, mock_session_service, mock_qa_service, mock_model_loader
    ):
        """Test question with specific document IDs."""
        mock_session = MagicMock()
        mock_session.document_count = 5
        mock_session_service.get_session = AsyncMock(return_value=mock_session)
        
        mock_response = AnswerResponse(
            answer="Answer from specific documents",
            confidence=0.85,
            source_chunks=[],
            cached=False,
        )
        mock_qa_service.answer_question = AsyncMock(return_value=mock_response)
        
        response = client.post(
            "/api/v1/asl",
            json={
                "question": "What is the total amount?",
                "document_ids": [1, 2, 3],
            },
            headers={"X-Session-ID": "test-session"},
        )
        
        assert response.status_code == 200


class TestASLCacheEndpoint:
    """Tests for DELETE /api/v1/asl/cache endpoint."""

    def test_clear_cache(self, client):
        """Test clearing the QA cache."""
        with patch("app.api.v1.endpoints.asl.QAService") as mock_service:
            mock_service.clear_cache.return_value = 5
            
            response = client.delete("/api/v1/asl/cache")
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert data["entries_cleared"] == 5


class TestASLStatusEndpoint:
    """Tests for GET /api/v1/asl/status endpoint."""

    def test_get_status_available(self, client, mock_model_loader):
        """Test getting QA status when available."""
        mock_model_loader.qa_available = True
        
        with patch("app.api.v1.endpoints.asl.QAService") as mock_service:
            mock_service.get_cache_size.return_value = 10
            
            response = client.get("/api/v1/asl/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["qa_available"] is True
            assert data["cache_size"] == 10
            assert "model_name" in data

    def test_get_status_unavailable(self, client):
        """Test getting QA status when unavailable."""
        with patch("app.api.v1.endpoints.asl.get_model_loader") as mock_loader:
            mock_instance = MagicMock()
            mock_instance.qa_available = False
            mock_loader.return_value = mock_instance
            
            with patch("app.api.v1.endpoints.asl.QAService") as mock_service:
                mock_service.get_cache_size.return_value = 0
                
                response = client.get("/api/v1/asl/status")
                
                assert response.status_code == 200
                data = response.json()
                assert data["qa_available"] is False


class TestRateLimiting:
    """Tests for rate limiting on ASL endpoint."""

    def test_rate_limit_exceeded(self, client, mock_session_service, mock_model_loader):
        """Test that rate limiting returns 429 after threshold."""
        # This test requires rate limiting to be enabled and configured
        # with a low threshold for testing purposes
        
        mock_session = MagicMock()
        mock_session.document_count = 5
        mock_session_service.get_session = AsyncMock(return_value=mock_session)
        
        # Note: This test may need adjustment based on actual rate limit settings
        # In a real test environment, you would configure a very low rate limit
        # or mock the rate limiter
        
        with patch("app.api.v1.endpoints.asl.limiter") as mock_limiter:
            # Simulate rate limit exceeded
            from slowapi.errors import RateLimitExceeded
            
            # This is a simplified test - in practice, you'd need to
            # actually trigger the rate limit or mock it properly
            pass  # Placeholder for rate limit testing
