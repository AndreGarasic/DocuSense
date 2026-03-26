"""
DocuSense - Embedding Service
"""
import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""

    _model: SentenceTransformer | None = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """Get or create the embedding model (singleton pattern)."""
        if cls._model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            cls._model = SentenceTransformer(settings.embedding_model)
            logger.info("Embedding model loaded successfully")
        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> list[float]:
        """Generate embedding for a single text."""
        model = cls.get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    @classmethod
    def generate_embeddings(cls, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts (batch processing)."""
        if not texts:
            return []
        model = cls.get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()

    @classmethod
    def get_embedding_dimension(cls) -> int:
        """Get the dimension of the embedding model."""
        return settings.embedding_dimension


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Get cached embedding service instance."""
    return EmbeddingService()
