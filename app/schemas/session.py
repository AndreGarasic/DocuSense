"""
DocuSense - Session Schemas
"""
from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Schema for creating a new session."""

    expires_in_hours: int | None = Field(
        default=24,
        ge=1,
        le=168,  # Max 1 week
        description="Session expiration time in hours",
    )


class SessionResponse(BaseModel):
    """Schema for session response."""

    id: str = Field(..., description="Session ID (UUID)")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime | None = Field(None, description="Session expiration timestamp")

    model_config = {"from_attributes": True}
