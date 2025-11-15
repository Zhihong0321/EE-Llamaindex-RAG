"""Message management service for handling conversation history."""

from datetime import datetime
from typing import List
from llama_index.core.llms import ChatMessage, MessageRole as LlamaMessageRole

from app.db.database import Database
from app.models.database import Message, MessageRole
from app.logging_config import get_logger
from app.exceptions import MessageSaveError


logger = get_logger(__name__)


class MessageService:
    """Service for managing conversation messages."""
    
    def __init__(self, db: Database):
        """Initialize MessageService with database connection.
        
        Args:
            db: Database instance for executing queries
        """
        self.db = db
    
    async def save_message(
        self, 
        session_id: str, 
        role: str, 
        content: str
    ) -> Message:
        """Save a message to the database.
        
        This method inserts a new message into the messages table with
        role validation. The role must be one of: 'user', 'assistant', 'system'.
        
        Args:
            session_id: Session identifier the message belongs to
            role: Message role (user, assistant, or system)
            content: Message content text
            
        Returns:
            Message object with id, session_id, role, content, and created_at
            
        Raises:
            ValueError: If role is not valid
            MessageSaveError: If saving the message fails
        """
        # Validate role
        try:
            message_role = MessageRole(role)
        except ValueError as e:
            logger.warning(
                "Invalid message role",
                extra={"session_id": session_id, "role": role}
            )
            raise ValueError(
                f"Invalid role '{role}'. Must be one of: user, assistant, system"
            ) from e
        
        try:
            logger.debug(
                "Saving message",
                extra={
                    "session_id": session_id,
                    "role": role,
                    "content_length": len(content)
                }
            )
            
            now = datetime.now()
            query = """
                INSERT INTO messages (session_id, role, content, created_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id, session_id, role, content, created_at
            """
            
            row = await self.db.fetchrow(query, session_id, role, content, now)
            
            message = Message(
                id=row['id'],
                session_id=row['session_id'],
                role=MessageRole(row['role']),
                content=row['content'],
                created_at=row['created_at']
            )
            
            logger.info(
                "Message saved successfully",
                extra={
                    "session_id": session_id,
                    "message_id": message.id,
                    "role": role
                }
            )
            
            return message
            
        except Exception as e:
            logger.error(
                "Failed to save message",
                extra={"session_id": session_id, "role": role, "error": str(e)},
                exc_info=True
            )
            raise MessageSaveError(session_id=session_id, reason=str(e)) from e
    
    async def get_recent_messages(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[Message]:
        """Get recent messages for a session.
        
        This method retrieves the most recent messages for a given session,
        ordered by created_at in descending order (newest first), then
        returns them in chronological order (oldest first) for chat context.
        
        Args:
            session_id: Session identifier to retrieve messages for
            limit: Maximum number of messages to retrieve (default: 10)
            
        Returns:
            List of Message objects in chronological order (oldest first)
        """
        logger.debug(
            "Retrieving recent messages",
            extra={"session_id": session_id, "limit": limit}
        )
        
        query = """
            SELECT id, session_id, role, content, created_at
            FROM messages
            WHERE session_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        
        rows = await self.db.fetch(query, session_id, limit)
        
        # Convert rows to Message objects and reverse to get chronological order
        messages = [
            Message(
                id=row['id'],
                session_id=row['session_id'],
                role=MessageRole(row['role']),
                content=row['content'],
                created_at=row['created_at']
            )
            for row in reversed(rows)
        ]
        
        logger.info(
            "Retrieved recent messages",
            extra={"session_id": session_id, "count": len(messages)}
        )
        
        return messages
    
    def format_for_chat_engine(self, messages: List[Message]) -> List[ChatMessage]:
        """Convert Message objects to LlamaIndex ChatMessage format.
        
        This method transforms database Message objects into the format
        expected by LlamaIndex's chat engine.
        
        Args:
            messages: List of Message objects from database
            
        Returns:
            List of ChatMessage objects for LlamaIndex
        """
        chat_messages = []
        
        for msg in messages:
            # Map our MessageRole to LlamaIndex MessageRole
            if msg.role == MessageRole.USER:
                llama_role = LlamaMessageRole.USER
            elif msg.role == MessageRole.ASSISTANT:
                llama_role = LlamaMessageRole.ASSISTANT
            elif msg.role == MessageRole.SYSTEM:
                llama_role = LlamaMessageRole.SYSTEM
            else:
                # Fallback, though this shouldn't happen with enum validation
                llama_role = LlamaMessageRole.USER
            
            chat_messages.append(
                ChatMessage(role=llama_role, content=msg.content)
            )
        
        return chat_messages
