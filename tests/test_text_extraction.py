"""
DocuSense - Text Extraction Service Tests

Unit tests for the TextExtractionService.
"""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.text_extraction_service import TextExtractionService


@pytest.fixture
def text_extraction_service():
    """Create a TextExtractionService instance with mocked model loader."""
    with patch("app.services.text_extraction_service.get_model_loader") as mock_loader:
        mock_instance = MagicMock()
        mock_instance.ocr_available = True
        mock_instance.ocr_reader = MagicMock()
        mock_loader.return_value = mock_instance
        
        service = TextExtractionService()
        yield service


@pytest.fixture
def sample_text_file():
    """Create a temporary text file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("This is a sample text document.\nIt has multiple lines.\nFor testing purposes.")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def sample_markdown_file():
    """Create a temporary markdown file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("# Heading\n\nThis is **markdown** content.\n\n- Item 1\n- Item 2")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def empty_text_file():
    """Create an empty text file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestTextExtractionService:
    """Tests for TextExtractionService."""

    @pytest.mark.asyncio
    async def test_extract_text_from_text_file(
        self, text_extraction_service, sample_text_file
    ):
        """Test extracting text from a plain text file."""
        result = await text_extraction_service.extract_text(sample_text_file)
        
        assert "This is a sample text document." in result
        assert "It has multiple lines." in result
        assert "For testing purposes." in result

    @pytest.mark.asyncio
    async def test_extract_text_from_markdown_file(
        self, text_extraction_service, sample_markdown_file
    ):
        """Test extracting text from a markdown file."""
        result = await text_extraction_service.extract_text(sample_markdown_file)
        
        assert "# Heading" in result
        assert "**markdown**" in result
        assert "- Item 1" in result

    @pytest.mark.asyncio
    async def test_extract_text_from_empty_file(
        self, text_extraction_service, empty_text_file
    ):
        """Test extracting text from an empty file."""
        result = await text_extraction_service.extract_text(empty_text_file)
        
        assert result == ""

    @pytest.mark.asyncio
    async def test_extract_text_from_nonexistent_file(self, text_extraction_service):
        """Test extracting text from a file that doesn't exist."""
        nonexistent_path = Path("/nonexistent/path/file.txt")
        
        result = await text_extraction_service.extract_text(nonexistent_path)
        
        assert result == ""

    @pytest.mark.asyncio
    async def test_extract_text_from_unsupported_file_type(
        self, text_extraction_service
    ):
        """Test extracting text from an unsupported file type."""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".xyz", delete=False
        ) as f:
            f.write(b"binary content")
            temp_path = Path(f.name)
        
        try:
            result = await text_extraction_service.extract_text(temp_path)
            assert result == ""
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @pytest.mark.asyncio
    async def test_extract_text_with_encoding_fallback(self, text_extraction_service):
        """Test extracting text with encoding fallback (latin-1)."""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".txt", delete=False
        ) as f:
            # Write content with latin-1 encoding that would fail UTF-8
            f.write("Café résumé naïve".encode("latin-1"))
            temp_path = Path(f.name)
        
        try:
            result = await text_extraction_service.extract_text(temp_path)
            # Should successfully extract with fallback encoding
            assert "Caf" in result  # At least partial content
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestTextExtractionServicePDF:
    """Tests for PDF extraction (requires PyMuPDF)."""

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_mocked(self, text_extraction_service):
        """Test PDF extraction with mocked PyMuPDF."""
        with patch(
            "app.services.text_extraction_service.TextExtractionService._extract_from_pdf_sync"
        ) as mock_extract:
            mock_extract.return_value = "Extracted PDF content"
            
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".pdf", delete=False
            ) as f:
                f.write(b"%PDF-1.4 fake pdf content")
                temp_path = Path(f.name)
            
            try:
                result = await text_extraction_service.extract_text(temp_path)
                assert result == "Extracted PDF content"
                mock_extract.assert_called_once()
            finally:
                if temp_path.exists():
                    temp_path.unlink()


class TestTextExtractionServiceImage:
    """Tests for image extraction (requires EasyOCR)."""

    @pytest.mark.asyncio
    async def test_extract_text_from_image_mocked(self, text_extraction_service):
        """Test image extraction with mocked OCR."""
        with patch(
            "app.services.text_extraction_service.TextExtractionService._extract_from_image_sync"
        ) as mock_extract:
            mock_extract.return_value = "OCR extracted text"
            
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".png", delete=False
            ) as f:
                # Write minimal PNG header
                f.write(b"\x89PNG\r\n\x1a\n")
                temp_path = Path(f.name)
            
            try:
                result = await text_extraction_service.extract_text(temp_path)
                assert result == "OCR extracted text"
                mock_extract.assert_called_once()
            finally:
                if temp_path.exists():
                    temp_path.unlink()

    @pytest.mark.asyncio
    async def test_extract_text_from_image_ocr_unavailable(self):
        """Test image extraction when OCR is unavailable."""
        with patch("app.services.text_extraction_service.get_model_loader") as mock_loader:
            mock_instance = MagicMock()
            mock_instance.ocr_available = False
            mock_instance.ocr_reader = None
            mock_loader.return_value = mock_instance
            
            service = TextExtractionService()
            
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".png", delete=False
            ) as f:
                f.write(b"\x89PNG\r\n\x1a\n")
                temp_path = Path(f.name)
            
            try:
                result = await service.extract_text(temp_path)
                assert result == ""
            finally:
                if temp_path.exists():
                    temp_path.unlink()


class TestTextExtractionServiceFileTypes:
    """Tests for file type detection."""

    def test_text_extensions(self):
        """Test that text extensions are correctly defined."""
        service = TextExtractionService()
        
        assert ".txt" in service.TEXT_EXTENSIONS
        assert ".md" in service.TEXT_EXTENSIONS
        assert ".text" in service.TEXT_EXTENSIONS
        assert ".markdown" in service.TEXT_EXTENSIONS

    def test_pdf_extensions(self):
        """Test that PDF extensions are correctly defined."""
        service = TextExtractionService()
        
        assert ".pdf" in service.PDF_EXTENSIONS

    def test_image_extensions(self):
        """Test that image extensions are correctly defined."""
        service = TextExtractionService()
        
        assert ".png" in service.IMAGE_EXTENSIONS
        assert ".jpg" in service.IMAGE_EXTENSIONS
        assert ".jpeg" in service.IMAGE_EXTENSIONS
        assert ".tiff" in service.IMAGE_EXTENSIONS
        assert ".bmp" in service.IMAGE_EXTENSIONS
