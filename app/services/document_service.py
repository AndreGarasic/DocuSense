"""
DocuSense - Document Service
"""
import hashlib
import logging
import os
import re
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentService:
    """Service for managing documents."""

    # Chunk size for text splitting (characters)
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    def __init__(self, db: AsyncSession):
        self.db = db
        self.upload_dir = settings.upload_dir

    async def _ensure_upload_dir(self, session_id: str) -> Path:
        """Ensure the upload directory exists for a session."""
        session_dir = self.upload_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def _generate_filename(self, original_filename: str) -> str:
        """Generate a unique filename while preserving extension."""
        ext = Path(original_filename).suffix.lower()
        unique_id = uuid.uuid4().hex[:12]
        safe_name = re.sub(r"[^\w\-.]", "_", Path(original_filename).stem)[:50]
        return f"{safe_name}_{unique_id}{ext}"

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    async def _extract_text(self, file_path: Path, content_type: str | None) -> str:
        """Extract text content from a file."""
        # For now, support plain text files
        # TODO: Add PDF, DOCX extraction with appropriate libraries
        text_types = {"text/plain", "text/markdown", "application/octet-stream"}
        text_extensions = {".txt", ".md", ".text", ".markdown"}

        ext = file_path.suffix.lower()

        if content_type in text_types or ext in text_extensions:
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    return await f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                async with aiofiles.open(file_path, "r", encoding="latin-1") as f:
                    return await f.read()

        # For unsupported types, return empty string
        logger.warning(f"Text extraction not supported for {content_type} ({ext})")
        return ""

    def _split_text_into_chunks(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.CHUNK_SIZE

            # Try to break at sentence or paragraph boundary
            if end < text_length:
                # Look for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + self.CHUNK_SIZE // 2:
                    end = para_break + 2
                else:
                    # Look for sentence break
                    sentence_break = max(
                        text.rfind(". ", start, end),
                        text.rfind("! ", start, end),
                        text.rfind("? ", start, end),
                    )
                    if sentence_break > start + self.CHUNK_SIZE // 2:
                        end = sentence_break + 2

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.CHUNK_OVERLAP if end < text_length else text_length

        return chunks

    async def upload_document(
        self,
        file: UploadFile,
        session_id: str,
        generate_embeddings: bool = True,
    ) -> Document:
        """Upload a single document."""
        # Ensure upload directory exists
        session_dir = await self._ensure_upload_dir(session_id)

        # Generate unique filename
        filename = self._generate_filename(file.filename or "unnamed")
        file_path = session_dir / filename

        # Save file to disk
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
            file_size = len(content)

        # Calculate file hash
        file_hash = await self._calculate_file_hash(file_path)

        # Extract text content
        content_text = await self._extract_text(file_path, file.content_type)

        # Create document record
        document = Document(
            session_id=session_id,
            filename=filename,
            original_filename=file.filename or "unnamed",
            content_type=file.content_type,
            file_size=file_size,
            file_path=str(file_path),
            file_hash=file_hash,
            content_text=content_text if content_text else None,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        # Create chunks and embeddings
        if content_text and generate_embeddings:
            await self._create_chunks_with_embeddings(document, content_text)

        # After creating chunks, refresh with eager load
        await self.db.refresh(document, ["chunks"])
        return document

    async def _create_chunks_with_embeddings(
        self, document: Document, text: str
    ) -> list[DocumentChunk]:
        """Create text chunks with embeddings for a document."""
        chunks_text = self._split_text_into_chunks(text)
        if not chunks_text:
            return []

        # Generate embeddings in batch
        embeddings = EmbeddingService.generate_embeddings(chunks_text)

        # Create chunk records
        chunks = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunks_text, embeddings)):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                content=chunk_text,
                embedding=embedding,
                metadata_={"char_count": len(chunk_text)},
            )
            self.db.add(chunk)
            chunks.append(chunk)

        await self.db.flush()
        return chunks

    async def upload_documents(
        self,
        files: list[UploadFile],
        session_id: str,
        generate_embeddings: bool = True,
    ) -> list[Document]:
        """Upload multiple documents."""
        documents = []
        for file in files:
            doc = await self.upload_document(file, session_id, generate_embeddings)
            documents.append(doc)
        return documents

    async def get_document(self, document_id: int, session_id: str) -> Document | None:
        """Get a document by ID and session."""
        result = await self.db.execute(
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.id == document_id, Document.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_documents_by_session(self, session_id: str) -> list[Document]:
        """Get all documents for a session."""
        result = await self.db.execute(
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.session_id == session_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_document_count(self, session_id: str) -> int:
        """Get the count of documents for a session."""
        result = await self.db.execute(
            select(func.count(Document.id)).where(Document.session_id == session_id)
        )
        return result.scalar() or 0

    async def delete_document(self, document_id: int, session_id: str) -> bool:
        """Delete a document and its file."""
        document = await self.get_document(document_id, session_id)
        if not document:
            return False

        # Delete file from disk
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        await self.db.delete(document)
        await self.db.flush()
        return True
