"""
DocuSense - Document Upload Endpoints
"""
import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import User, get_current_active_user
from app.db.session import get_db
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.schemas.session import SessionResponse
from app.services.document_service import DocumentService
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/upload", tags=["upload"])


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file size
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.max_file_size // (1024 * 1024)}MB",
        )

    # Check file extension
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type '{ext}' not allowed. Allowed types: {settings.allowed_extensions}",
            )


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload documents",
    description="Upload one or more documents. Returns a session ID for retrieval. **Requires authentication.**",
)
async def upload_documents(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
    x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
) -> DocumentUploadResponse:
    """
    Upload one or more documents.

    - **files**: One or more files to upload
    - **X-Session-ID**: Optional session ID header. If not provided, a new session is created.

    Returns the session ID and uploaded document details.
    """

    files = [file]

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )

    # Validate all files first
    for file in files:
        validate_file(file)

    # Get or create session
    session_service = SessionService(db)
    session = await session_service.get_or_create_session(x_session_id)

    # Upload documents
    document_service = DocumentService(db)
    documents = await document_service.upload_documents(files, session.id)

    # Build response
    doc_responses = [
        DocumentResponse(
            id=doc.id,
            session_id=doc.session_id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            content_type=doc.content_type,
            file_size=doc.file_size,
            created_at=doc.created_at,
            chunk_count=len(doc.chunks) if doc.chunks else 0,
        )
        for doc in documents
    ]

    logger.info(f"User '{current_user.username}' uploaded {len(documents)} document(s)")

    return DocumentUploadResponse(
        message=f"Successfully uploaded {len(documents)} document(s)",
        session_id=session.id,
        documents=doc_responses,
        total_uploaded=len(documents),
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List documents",
    description="List all documents for a session. **Requires authentication.**",
)
async def list_documents(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_session_id: Annotated[str, Header(alias="X-Session-ID")],
) -> DocumentListResponse:
    """
    List all documents for a session.

    - **X-Session-ID**: Required session ID header.
    """
    # Validate session
    session_service = SessionService(db)
    if not await session_service.is_session_valid(x_session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired",
        )

    # Get documents
    document_service = DocumentService(db)
    documents = await document_service.get_documents_by_session(x_session_id)

    doc_responses = [
        DocumentResponse(
            id=doc.id,
            session_id=doc.session_id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            content_type=doc.content_type,
            file_size=doc.file_size,
            created_at=doc.created_at,
            chunk_count=len(doc.chunks) if doc.chunks else 0,
        )
        for doc in documents
    ]

    return DocumentListResponse(
        session_id=x_session_id,
        documents=doc_responses,
        total=len(doc_responses),
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document",
    description="Get a specific document by ID. **Requires authentication.**",
)
async def get_document(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_session_id: Annotated[str, Header(alias="X-Session-ID")],
) -> DocumentResponse:
    """
    Get a specific document by ID.

    - **document_id**: Document ID
    - **X-Session-ID**: Required session ID header.
    """
    # Validate session
    session_service = SessionService(db)
    if not await session_service.is_session_valid(x_session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired",
        )

    # Get document
    document_service = DocumentService(db)
    document = await document_service.get_document(document_id, x_session_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentResponse(
        id=document.id,
        session_id=document.session_id,
        filename=document.filename,
        original_filename=document.original_filename,
        content_type=document.content_type,
        file_size=document.file_size,
        created_at=document.created_at,
        chunk_count=len(document.chunks) if document.chunks else 0,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Delete a specific document by ID. **Requires authentication.**",
)
async def delete_document(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_session_id: Annotated[str, Header(alias="X-Session-ID")],
) -> None:
    """
    Delete a specific document by ID.

    - **document_id**: Document ID
    - **X-Session-ID**: Required session ID header.
    """
    # Validate session
    session_service = SessionService(db)
    if not await session_service.is_session_valid(x_session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired",
        )

    # Delete document
    document_service = DocumentService(db)
    deleted = await document_service.delete_document(document_id, x_session_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    logger.info(f"User '{current_user.username}' deleted document {document_id}")


@router.post(
    "/session",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create session",
    description="Create a new session for document uploads. **Requires authentication.**",
)
async def create_session(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    expires_in_hours: int = 24,
) -> SessionResponse:
    """
    Create a new session for document uploads.

    - **expires_in_hours**: Session expiration time in hours (default: 24, max: 168)
    """
    session_service = SessionService(db)
    session = await session_service.create_session(expires_in_hours)

    logger.info(f"User '{current_user.username}' created session {session.id}")

    return SessionResponse(
        id=session.id,
        created_at=session.created_at,
        expires_at=session.expires_at,
    )
