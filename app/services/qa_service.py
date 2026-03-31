"""
DocuSense - QA Service

Question-Answering service with caching support.
Uses pgvector for semantic search and DistilBERT for answer extraction.
"""
import asyncio
import hashlib
import logging
from typing import Any

from cachetools import TTLCache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.qa import AnswerResponse, ChunkReference
from app.services.embedding_service import EmbeddingService
from app.services.model_loader import get_model_loader

logger = logging.getLogger(__name__)
settings = get_settings()


class QAService:
    """
    Question-Answering service with caching.
    
    Features:
    - Semantic search using pgvector cosine similarity
    - Answer extraction using DistilBERT QA pipeline
    - TTL-based caching for repeated questions
    """

    # Class-level cache shared across instances
    _cache: TTLCache | None = None

    def __init__(self, db: AsyncSession):
        self.db = db
        self._model_loader = get_model_loader()
        self._ensure_cache()

    @classmethod
    def _ensure_cache(cls) -> None:
        """Ensure the cache is initialized."""
        if cls._cache is None:
            cls._cache = TTLCache(
                maxsize=settings.cache_max_size,
                ttl=settings.cache_ttl_seconds,
            )

    @classmethod
    def clear_cache(cls) -> int:
        """
        Clear the answer cache.
        
        Returns the number of entries cleared.
        """
        if cls._cache is None:
            return 0
        count = len(cls._cache)
        cls._cache.clear()
        logger.info(f"Cleared {count} entries from QA cache")
        return count

    @classmethod
    def get_cache_size(cls) -> int:
        """Get the current cache size."""
        if cls._cache is None:
            return 0
        return len(cls._cache)

    def _generate_cache_key(
        self,
        question: str,
        session_id: str,
        document_ids: list[int] | None,
    ) -> str:
        """
        Generate a cache key for a question.
        
        Key is based on normalized question, session ID, and document IDs.
        """
        # Normalize question (lowercase, strip whitespace)
        normalized_question = question.lower().strip()
        
        # Sort document IDs for consistent hashing
        doc_ids_str = ",".join(map(str, sorted(document_ids))) if document_ids else "all"
        
        # Create hash
        key_string = f"{session_id}:{doc_ids_str}:{normalized_question}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def answer_question(
        self,
        question: str,
        session_id: str,
        document_ids: list[int] | None = None,
    ) -> AnswerResponse:
        """
        Answer a question based on uploaded documents.
        
        Args:
            question: The question to answer
            session_id: Session ID for document filtering
            document_ids: Optional list of specific document IDs to search
            
        Returns:
            AnswerResponse with answer, confidence, and source references
        """
        # Check cache first
        cache_key = self._generate_cache_key(question, session_id, document_ids)
        if self._cache is not None and cache_key in self._cache:
            logger.debug(f"Cache hit for question: {question[:50]}...")
            cached_response = self._cache[cache_key]
            cached_response.cached = True
            return cached_response

        # Check if QA model is available
        if not self._model_loader.qa_available:
            logger.warning("QA model not available")
            return AnswerResponse(
                answer="QA service is currently unavailable. Please try again later.",
                confidence=0.0,
                source_chunks=[],
                cached=False,
            )

        # Retrieve relevant chunks
        chunks = await self._retrieve_relevant_chunks(
            question, session_id, document_ids
        )

        if not chunks:
            return AnswerResponse(
                answer="No relevant documents found to answer your question. Please upload documents first.",
                confidence=0.0,
                source_chunks=[],
                cached=False,
            )

        # Build context from chunks
        context, chunk_references = self._build_context(chunks)

        # Run QA model
        answer, confidence = await self._run_qa_model(question, context)

        # Create response
        response = AnswerResponse(
            answer=answer,
            confidence=confidence,
            source_chunks=chunk_references,
            cached=False,
        )

        # Cache the response
        if self._cache is not None:
            self._cache[cache_key] = response

        return response

    async def _retrieve_relevant_chunks(
        self,
        question: str,
        session_id: str,
        document_ids: list[int] | None,
    ) -> list[tuple[DocumentChunk, Document, float]]:
        """
        Retrieve relevant chunks using pgvector cosine similarity.
        
        Returns list of (chunk, document, similarity_score) tuples.
        """
        # Generate question embedding
        question_embedding = await asyncio.to_thread(
            EmbeddingService.generate_embedding, question
        )

        # Build query with cosine similarity
        # pgvector uses <=> for cosine distance (1 - similarity)
        similarity_expr = (
            1 - DocumentChunk.embedding.cosine_distance(question_embedding)
        ).label("similarity")

        query = (
            select(DocumentChunk, Document, similarity_expr)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.session_id == session_id)
            .where(DocumentChunk.embedding.isnot(None))
        )

        # Filter by document IDs if specified
        if document_ids:
            query = query.where(Document.id.in_(document_ids))

        # Order by similarity and limit
        query = query.order_by(similarity_expr.desc()).limit(settings.qa_top_k_chunks)

        result = await self.db.execute(query)
        rows = result.all()

        return [(row[0], row[1], row[2]) for row in rows]

    def _build_context(
        self,
        chunks: list[tuple[DocumentChunk, Document, float]],
    ) -> tuple[str, list[ChunkReference]]:
        """
        Build context string from chunks and create chunk references.
        
        Truncates context to fit within model's max length.
        """
        context_parts = []
        chunk_references = []
        total_length = 0
        max_length = settings.qa_max_context_length * 4  # Approximate chars per token

        for chunk, document, similarity in chunks:
            chunk_text = chunk.content

            # Check if adding this chunk would exceed max length
            if total_length + len(chunk_text) > max_length:
                # Truncate the chunk to fit
                remaining = max_length - total_length
                if remaining > 100:  # Only add if meaningful content remains
                    chunk_text = chunk_text[:remaining] + "..."
                else:
                    break

            context_parts.append(chunk_text)
            total_length += len(chunk_text)

            # Create chunk reference
            content_preview = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
            chunk_references.append(
                ChunkReference(
                    document_id=document.id,
                    filename=document.original_filename,
                    chunk_index=chunk.chunk_index,
                    content_preview=content_preview,
                    similarity_score=round(max(0.0, similarity), 4),
                )
            )

        context = "\n\n".join(context_parts)
        return context, chunk_references

    async def _run_qa_model(
        self,
        question: str,
        context: str,
    ) -> tuple[str, float]:
        """
        Run the QA model to extract an answer.
        
        Returns (answer, confidence) tuple.
        """
        if not context:
            return "No context available to answer the question.", 0.0

        try:
            # Run in thread pool to avoid blocking
            result = await asyncio.to_thread(
                self._run_qa_model_sync, question, context
            )
            return result
        except Exception as e:
            logger.error(f"Error running QA model: {e}")
            return "An error occurred while processing your question.", 0.0

    def _run_qa_model_sync(
        self,
        question: str,
        context: str,
    ) -> tuple[str, float]:
        """Synchronous QA model execution."""
        qa_pipeline = self._model_loader.qa_pipeline
        if qa_pipeline is None:
            return "QA model not available.", 0.0

        try:
            result = qa_pipeline(question=question, context=context)
            answer = result.get("answer", "")
            confidence = result.get("score", 0.0)

            # Handle empty or low-confidence answers
            if not answer or confidence < 0.01:
                return "I couldn't find a confident answer to your question in the provided documents.", confidence

            return answer, confidence

        except Exception as e:
            logger.error(f"QA pipeline error: {e}")
            return "Error processing question.", 0.0


def get_qa_service(db: AsyncSession) -> QAService:
    """Get a QA service instance."""
    return QAService(db)
