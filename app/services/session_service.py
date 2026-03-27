"""
DocuSense - Session Service
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import Session


class SessionService:
    """Service for managing sessions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, expires_in_hours: int | None = 24) -> Session:
        """Create a new session."""
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        session = Session(expires_at=expires_at)
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session(
        self, session_id: str, load_documents: bool = True
    ) -> Session | None:
        """
        Get a session by ID.
        
        Args:
            session_id: The session ID to look up
            load_documents: Whether to eagerly load documents (needed for document_count)
        """
        query = select(Session).where(Session.id == session_id)
        if load_documents:
            query = query.options(selectinload(Session.documents))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create_session(
        self, session_id: str | None = None, expires_in_hours: int | None = 24
    ) -> Session:
        """Get existing session or create a new one."""
        if session_id:
            session = await self.get_session(session_id)
            if session:
                # Check if session is expired
                if session.expires_at and session.expires_at < datetime.now(timezone.utc):
                    # Session expired, create new one
                    return await self.create_session(expires_in_hours)
                return session

        return await self.create_session(expires_in_hours)

    async def is_session_valid(self, session_id: str) -> bool:
        """Check if a session is valid and not expired."""
        session = await self.get_session(session_id)
        if not session:
            return False
        if session.expires_at and session.expires_at < datetime.now(timezone.utc):
            return False
        return True

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all associated documents."""
        session = await self.get_session(session_id)
        if not session:
            return False
        await self.db.delete(session)
        await self.db.flush()
        return True
