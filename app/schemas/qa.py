"""
DocuSense - QA Schemas

Pydantic schemas for the Question-Answering feature.
"""
from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """Request schema for asking a question."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="The question to ask about the uploaded documents",
        examples=["What is the total amount?", "Who are the parties in this contract?"],
    )
    document_ids: list[int] | None = Field(
        default=None,
        description="Optional list of document IDs to search. If not provided, searches all session documents.",
        examples=[[1, 2, 3]],
    )


class ChunkReference(BaseModel):
    """Reference to a source chunk used for answering."""

    document_id: int = Field(..., description="ID of the source document")
    filename: str = Field(..., description="Original filename of the document")
    chunk_index: int = Field(..., description="Index of the chunk within the document")
    content_preview: str = Field(
        ...,
        description="Preview of the chunk content (truncated)",
        max_length=500,
    )
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score between question and chunk",
    )


class AnswerResponse(BaseModel):
    """Response schema for a QA answer."""

    answer: str = Field(..., description="The answer to the question")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the answer (0-1)",
    )
    source_chunks: list[ChunkReference] = Field(
        default_factory=list,
        description="List of source chunks used to generate the answer",
    )
    cached: bool = Field(
        default=False,
        description="Whether this answer was retrieved from cache",
    )


class QAErrorResponse(BaseModel):
    """Error response schema for QA operations."""

    detail: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code for programmatic handling")


class QAStatusResponse(BaseModel):
    """Response schema for QA service status."""

    qa_available: bool = Field(..., description="Whether QA service is available")
    cache_size: int = Field(..., description="Current number of cached answers")
    model_name: str = Field(..., description="Name of the QA model being used")
