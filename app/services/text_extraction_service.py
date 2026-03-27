"""
DocuSense - Text Extraction Service

Extracts text from various file types including PDFs, images, and text files.
Uses PyMuPDF for PDFs and EasyOCR for images/scanned documents.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any

import aiofiles

from app.core.config import get_settings
from app.services.model_loader import get_model_loader

logger = logging.getLogger(__name__)
settings = get_settings()


class TextExtractionService:
    """
    Service for extracting text from various document types.
    
    Supports:
    - PDFs (text-based and scanned with OCR fallback)
    - Images (PNG, JPG, JPEG, TIFF, BMP)
    - Plain text files (TXT, MD)
    """

    # File type categories
    TEXT_EXTENSIONS = {".txt", ".md", ".text", ".markdown"}
    PDF_EXTENSIONS = {".pdf"}
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}

    # Threshold for detecting scanned PDFs (characters per page)
    SCANNED_PDF_THRESHOLD = 50

    def __init__(self):
        self._model_loader = get_model_loader()

    async def extract_text(
        self,
        file_path: Path,
        content_type: str | None = None,
    ) -> str:
        """
        Extract text from a file.
        
        Args:
            file_path: Path to the file
            content_type: MIME type of the file (optional)
            
        Returns:
            Extracted text content, or empty string if extraction fails
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return ""

        ext = file_path.suffix.lower()

        try:
            if ext in self.TEXT_EXTENSIONS:
                return await self._extract_from_text_file(file_path)
            elif ext in self.PDF_EXTENSIONS:
                return await self._extract_from_pdf(file_path)
            elif ext in self.IMAGE_EXTENSIONS:
                return await self._extract_from_image(file_path)
            else:
                logger.warning(f"Unsupported file type: {ext}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""

    async def _extract_from_text_file(self, file_path: Path) -> str:
        """Extract text from a plain text file."""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                return await f.read()
        except UnicodeDecodeError:
            # Try with fallback encoding
            try:
                async with aiofiles.open(file_path, "r", encoding="latin-1") as f:
                    return await f.read()
            except Exception as e:
                logger.error(f"Failed to read text file with fallback encoding: {e}")
                return ""

    async def _extract_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from a PDF file.
        
        Uses PyMuPDF for text extraction. If a page has very little text,
        it's assumed to be scanned and OCR is applied.
        """
        return await asyncio.to_thread(self._extract_from_pdf_sync, file_path)

    def _extract_from_pdf_sync(self, file_path: Path) -> str:
        """Synchronous PDF text extraction."""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(file_path))
            text_parts = []

            for page_num, page in enumerate(doc):
                # Try direct text extraction first
                page_text = page.get_text()

                # Check if page might be scanned (very little text)
                if len(page_text.strip()) < self.SCANNED_PDF_THRESHOLD:
                    logger.debug(
                        f"Page {page_num + 1} appears to be scanned, attempting OCR"
                    )
                    ocr_text = self._ocr_pdf_page(page)
                    if ocr_text:
                        page_text = ocr_text

                text_parts.append(page_text)

            doc.close()
            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def _ocr_pdf_page(self, page: Any) -> str:
        """Apply OCR to a PDF page."""
        if not self._model_loader.ocr_available:
            logger.warning("OCR not available, skipping scanned page")
            return ""

        try:
            import fitz  # PyMuPDF

            # Render page to image
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")

            # Use EasyOCR
            import io

            from PIL import Image

            image = Image.open(io.BytesIO(img_data))
            return self._ocr_image(image)

        except Exception as e:
            logger.error(f"Error during PDF page OCR: {e}")
            return ""

    async def _extract_from_image(self, file_path: Path) -> str:
        """Extract text from an image file using OCR."""
        return await asyncio.to_thread(self._extract_from_image_sync, file_path)

    def _extract_from_image_sync(self, file_path: Path) -> str:
        """Synchronous image text extraction."""
        if not self._model_loader.ocr_available:
            logger.warning("OCR not available, cannot extract text from image")
            return ""

        try:
            from PIL import Image

            image = Image.open(file_path)
            return self._ocr_image(image)

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""

    def _ocr_image(self, image: Any) -> str:
        """
        Apply OCR to a PIL Image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text
        """
        if not self._model_loader.ocr_available:
            return ""

        try:
            import numpy as np

            # Convert PIL Image to numpy array
            img_array = np.array(image)

            # Run OCR
            reader = self._model_loader.ocr_reader
            results = reader.readtext(img_array)

            # Extract text from results
            # EasyOCR returns list of (bbox, text, confidence)
            text_parts = [result[1] for result in results]
            return " ".join(text_parts)

        except Exception as e:
            logger.error(f"Error during OCR: {e}")
            return ""


# Singleton instance
_text_extraction_service: TextExtractionService | None = None


def get_text_extraction_service() -> TextExtractionService:
    """Get the text extraction service instance."""
    global _text_extraction_service
    if _text_extraction_service is None:
        _text_extraction_service = TextExtractionService()
    return _text_extraction_service
