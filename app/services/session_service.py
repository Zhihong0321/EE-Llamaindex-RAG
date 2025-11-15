"""Session management service for handling conversation sessions."""

from datetime import datetime
from typing import Optional
from app.db.database import Database
from app.models.database import Session
from app.logging_config import get_logger


logger = get_logger(__name__)


class SessionService:
    """Service for managing conversation sessions."""
    
    def __init__(self, db: Database):
        """Initialize SessionService with database connection.
        
        Args:
            db: Database instance for executing queries
        """
        self.db = db
    
    async def get_or_create_session(
        self, 
        session_id: str, 
        user_id: Optional[str] = None
    ) -> Session:
        """Get existing session or create new one if it doesn't exist.
        
        This method checks if a session with the given session_id exists.
        If it exists, returns the existing session. If not, creates a new
        session with the provided session_id and optional user_id.
        
        Args:
            session_id: Unique identifier for the session
            user_id: Optional user identifier associated with the session
            
        Returns:
            Session object with id, user_id, created_at, and last_active_at
        """
        logger.debug(
            "Getting or creating session",
            extra={"session_id": session_id, "user_id": user_id}
        )
        
        # Try to fetch existing session
        query = """
            SELECT id, user_id, created_at, last_active_at
            FROM sessions
            WHERE id = $1
        """
        row = await self.db.fetchrow(query, session_id)
        
        if row:
            # Session exists, return it
            logger.info(
                "Session found",
                extra={"session_id": session_id}
            )
            return Session(
                id=row['id'],
                user_id=row['user_id'],
                created_at=row['created_at'],
                last_active_at=row['last_active_at']
            )
        
        # Session doesn't exist, create new one
        logger.info(
            "Creating new session",
            extra={"session_id": session_id, "user_id": user_id}
        )
        
        now = datetime.now()
        insert_query = """
            INSERT INTO sessions (id, user_id, created_at, last_active_at)
            VALUES ($1, $2, $3, $4)
            RETURNING id, user_id, created_at, last_active_at
        """
        row = await self.db.fetchrow(insert_query, session_id, user_id, now, now)
        
        logger.info(
            "Session created successfully",
            extra={"session_id": session_id}
        )
        
        return Session(
            id=row['id'],
            user_id=row['user_id'],
            created_at=row['created_at'],
            last_active_at=row['last_active_at']
        )
    
    async def update_last_active(self, session_id: str) -> None:
        """Update the last_active_at timestamp for a session.
        
        This method updates the last_active_at field to the current timestamp,
        indicating that the session has been recently used.
        
        Args:
            session_id: Unique identifier for the session to update
        """
        logger.debug(
            "Updating session last_active_at",
            extra={"session_id": session_id}
        )
        
        now = datetime.now()
        query = """
            UPDATE sessions
            SET last_active_at = $1
            WHERE id = $2
        """
        await self.db.execute(query, now, session_id)
        
        logger.debug(
            "Session last_active_at updated",
            extra={"session_id": session_id}
        )
