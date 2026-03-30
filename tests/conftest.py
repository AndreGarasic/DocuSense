"""
DocuSense - Test Configuration and Fixtures
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


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


# ============================================
# QA Testing Fixtures
# ============================================


@pytest.fixture
def sample_pdf_path() -> Path:
    """Path to sample PDF fixture."""
    # Try PDF first, fall back to text version
    pdf_path = FIXTURES_DIR / "sample_invoice.pdf"
    if pdf_path.exists():
        return pdf_path
    return FIXTURES_DIR / "sample_invoice.txt"


@pytest.fixture
def sample_contract_path() -> Path:
    """Path to sample contract fixture."""
    pdf_path = FIXTURES_DIR / "sample_contract.pdf"
    if pdf_path.exists():
        return pdf_path
    return FIXTURES_DIR / "sample_contract.txt"


@pytest.fixture
def sample_image_path() -> Path:
    """Path to sample image fixture."""
    return FIXTURES_DIR / "scanned_receipt.png"


@pytest.fixture
def sample_text_path() -> Path:
    """Path to sample text document fixture."""
    return FIXTURES_DIR / "sample_document.txt"


@pytest.fixture
def mock_model_loader():
    """
    Mocked model loader that returns predictable responses for unit tests.
    
    This fixture patches the model loader to avoid loading actual ML models
    during testing, which would be slow and resource-intensive.
    """
    with patch("app.services.model_loader.get_model_loader") as mock_get_loader:
        mock_loader = MagicMock()
        
        # Mock OCR reader
        mock_loader.ocr_available = True
        mock_loader.ocr_reader = MagicMock()
        mock_loader.ocr_reader.readtext.return_value = [
            (None, "Mocked OCR text", 0.95),
        ]
        
        # Mock QA pipeline
        mock_loader.qa_available = True
        mock_loader.qa_pipeline = MagicMock()
        mock_loader.qa_pipeline.return_value = {
            "answer": "Mocked answer",
            "score": 0.85,
        }
        
        # Mock status
        mock_loader.get_status.return_value = {
            "ocr": {"initialized": True, "available": True, "error": None},
            "qa": {"initialized": True, "available": True, "error": None},
        }
        
        mock_get_loader.return_value = mock_loader
        yield mock_loader


@pytest.fixture
def mock_embedding_service():
    """
    Mocked embedding service for testing.
    
    Returns predictable embeddings without loading the actual model.
    """
    with patch("app.services.embedding_service.EmbeddingService") as mock_service:
        # Return a fixed-dimension embedding
        mock_service.generate_embedding.return_value = [0.1] * 384
        mock_service.generate_embeddings.return_value = [[0.1] * 384]
        mock_service.get_embedding_dimension.return_value = 384
        yield mock_service


@pytest.fixture
def mock_db_session():
    """
    Mocked async database session for testing.
    
    Provides a mock that can be used in place of the actual database session.
    """
    from unittest.mock import AsyncMock
    
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.delete = AsyncMock()
    
    return mock_session


@pytest.fixture
def sample_question_request():
    """Sample question request data for testing."""
    return {
        "question": "What is the total amount?",
        "document_ids": None,
    }


@pytest.fixture
def sample_question_with_docs():
    """Sample question request with document IDs."""
    return {
        "question": "What is the invoice number?",
        "document_ids": [1, 2],
    }
