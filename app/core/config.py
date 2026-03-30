"""
DocuSense - FastAPI Application Configuration
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "DocuSense API"
    app_version: str = "0.1.0"
    app_description: str = "A FastAPI REST API application for document insight"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Database settings
    database_url: str = "postgresql+asyncpg://docusense:docusense@localhost:5432/docusense"

    # File storage settings
    upload_dir: Path = Path("uploads")
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: set[str] = {
        ".pdf", ".txt", ".md", ".doc", ".docx",
        ".png", ".jpg", ".jpeg", ".tiff", ".bmp"
    }

    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384  # Dimension for all-MiniLM-L6-v2

    # OCR settings
    ocr_use_gpu: bool = False
    ocr_languages: list[str] = ["en"]

    # QA model settings
    qa_model_name: str = "distilbert/distilbert-base-cased-distilled-squad"
    qa_max_context_length: int = 512
    qa_top_k_chunks: int = 5

    # Rate limiting settings
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 30

    # Caching settings
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_max_size: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
