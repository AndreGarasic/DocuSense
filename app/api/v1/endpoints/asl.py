"""
DocuSense - ASL Endpoints

Question-Answering API endpoints with rate limiting.
"""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limiter import get_limiter, get_rate_limit_string
from app.db.session import get_db
from app.schemas.qa import (
    AnswerResponse,
    QAErrorResponse,
    QAStatusResponse,
    QuestionRequest,
)
from app.services.model_loader import get_model_loader
from app.services.qa_service import QAService
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)
settings = get_settings()
limiter = get_limiter()

router = APIRouter(prefix="/asl", tags=["Question Answering"])


@router.post(
    "",
    response_model=AnswerResponse,
    responses={
        404: {"model": QAErrorResponse, "description": "Session not found"},
        422: {"model": QAErrorResponse, "description": "Validation error"},
        429: {"model": QAErrorResponse, "description": "Rate limit exceeded"},
        503: {"model": QAErrorResponse, "description": "QA service unavailable"},
    },
    summary="Ask a question about uploaded documents",
    description="""
    Ask a question about the documents uploaded in the current session.
    
    The system will:
    1. Search for relevant document chunks using semantic similarity
    2. Use a QA model to extract the answer from the most relevant chunks
    3. Return the answer with confidence score and source references
    
    Answers are cached for repeated questions within the same session.
    """,
)
@limiter.limit(get_rate_limit_string())
async def ask_question(
    request: Request,
    body: QuestionRequest,
    x_session_id: str = Header(..., description="Session ID for document context"),
    db: AsyncSession = Depends(get_db),
) -> AnswerResponse:
    """
    Ask a question about uploaded documents.
    
    Requires a valid session ID with at least one uploaded document.
    """
    # Validate session exists
    session_service = SessionService(db)
    session = await session_service.get_session(x_session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{x_session_id}' not found",
        )

    # Check if session has documents
    if session.document_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded in this session. Please upload documents first.",
        )

    # Check if QA service is available
    model_loader = get_model_loader()
    if not model_loader.qa_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="QA service is currently unavailable. Please try again later.",
        )

    # Answer the question
    qa_service = QAService(db)
    response = await qa_service.answer_question(
        question=body.question,
        session_id=x_session_id,
        document_ids=body.document_ids,
    )

    return response


@router.delete(
    "/cache",
    response_model=dict,
    summary="Clear the QA answer cache",
    description="Administrative endpoint to clear all cached QA answers.",
)
async def clear_cache() -> dict:
    """
    Clear the QA answer cache.
    
    This is an administrative operation that clears all cached answers.
    """
    cleared_count = QAService.clear_cache()
    return {
        "message": "Cache cleared successfully",
        "entries_cleared": cleared_count,
    }


@router.get(
    "/status",
    response_model=QAStatusResponse,
    summary="Get QA service status",
    description="Check the status of the QA service including model availability and cache size.",
)
async def get_status() -> QAStatusResponse:
    """
    Get the status of the QA service.
    """
    model_loader = get_model_loader()
    return QAStatusResponse(
        qa_available=model_loader.qa_available,
        cache_size=QAService.get_cache_size(),
        model_name=settings.qa_model_name,
    )
