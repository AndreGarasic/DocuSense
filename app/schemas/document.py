"""
DocuSense - Document Schemas
"""
from datetime import datetime

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Schema for document creation (internal use)."""

    filename: str
    original_filename: str
    content_type: str | None = None
    file_size: int
    file_path: str
    file_hash: str | None = None


class DocumentResponse(BaseModel):
    """Schema for single document response."""

    id: int = Field(..., description="Document ID")
    session_id: str = Field(..., description="Session ID")
    filename: str = Field(..., description="Stored filename")
    original_filename: str = Field(..., description="Original uploaded filename")
    content_type: str | None = Field(None, description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Upload timestamp")
    chunk_count: int = Field(default=0, description="Number of text chunks")

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    """Schema for upload response."""

    message: str = Field(..., description="Status message")
    session_id: str = Field(..., description="Session ID for retrieval")
    documents: list[DocumentResponse] = Field(..., description="Uploaded documents")
    total_uploaded: int = Field(..., description="Total number of documents uploaded")


class DocumentListResponse(BaseModel):
    """Schema for listing documents."""

    session_id: str = Field(..., description="Session ID")
    documents: list[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
