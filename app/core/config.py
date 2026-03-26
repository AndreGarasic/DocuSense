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
    app_description: str = "A FastAPI REST API application for document management"
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
    allowed_extensions: set[str] = {".pdf", ".txt", ".md", ".doc", ".docx"}

    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384  # Dimension for all-MiniLM-L6-v2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
