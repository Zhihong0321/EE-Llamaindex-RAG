"""Custom exception classes for domain errors.

This module defines custom exceptions for different error scenarios
in the RAG API Server, enabling better error handling and user feedback.

Requirement 10.4: Proper error handling with clear error messages.
"""


class RAGAPIException(Exception):
    """Base exception for all RAG API errors."""
    
    def __init__(self, message: str, code: str = "RAG_API_ERROR"):
        """Initialize exception with message and error code.
        
        Args:
            message: Human-readable error message
            code: Machine-readable error code
        """
        self.message = message
        self.code = code
        super().__init__(self.message)


class SessionNotFoundError(RAGAPIException):
    """Raised when a session cannot be found."""
    
    def __init__(self, session_id: str):
        """Initialize with session ID.
        
        Args:
            session_id: The session ID that was not found
        """
        super().__init__(
            message=f"Session not found: {session_id}",
            code="SESSION_NOT_FOUND"
        )
        self.session_id = session_id


class DocumentIngestError(RAGAPIException):
    """Raised when document ingestion fails."""
    
    def __init__(self, document_id: str, reason: str):
        """Initialize with document ID and failure reason.
        
        Args:
            document_id: The document ID that failed to ingest
            reason: Reason for the failure
        """
        super().__init__(
            message=f"Failed to ingest document {document_id}: {reason}",
            code="DOCUMENT_INGEST_ERROR"
        )
        self.document_id = document_id
        self.reason = reason


class DocumentNotFoundError(RAGAPIException):
    """Raised when a document cannot be found."""
    
    def __init__(self, document_id: str):
        """Initialize with document ID.
        
        Args:
            document_id: The document ID that was not found
        """
        super().__init__(
            message=f"Document not found: {document_id}",
            code="DOCUMENT_NOT_FOUND"
        )
        self.document_id = document_id


class ChatGenerationError(RAGAPIException):
    """Raised when chat response generation fails."""
    
    def __init__(self, session_id: str, reason: str):
        """Initialize with session ID and failure reason.
        
        Args:
            session_id: The session ID where chat generation failed
            reason: Reason for the failure
        """
        super().__init__(
            message=f"Failed to generate chat response for session {session_id}: {reason}",
            code="CHAT_GENERATION_ERROR"
        )
        self.session_id = session_id
        self.reason = reason


class MessageSaveError(RAGAPIException):
    """Raised when saving a message fails."""
    
    def __init__(self, session_id: str, reason: str):
        """Initialize with session ID and failure reason.
        
        Args:
            session_id: The session ID where message save failed
            reason: Reason for the failure
        """
        super().__init__(
            message=f"Failed to save message for session {session_id}: {reason}",
            code="MESSAGE_SAVE_ERROR"
        )
        self.session_id = session_id
        self.reason = reason


class DatabaseConnectionError(RAGAPIException):
    """Raised when database connection fails."""
    
    def __init__(self, reason: str):
        """Initialize with failure reason.
        
        Args:
            reason: Reason for the connection failure
        """
        super().__init__(
            message=f"Database connection failed: {reason}",
            code="DATABASE_CONNECTION_ERROR"
        )
        self.reason = reason


class OpenAIServiceError(RAGAPIException):
    """Raised when OpenAI API calls fail."""
    
    def __init__(self, operation: str, reason: str):
        """Initialize with operation and failure reason.
        
        Args:
            operation: The operation that failed (e.g., "embedding", "chat")
            reason: Reason for the failure
        """
        super().__init__(
            message=f"OpenAI API error during {operation}: {reason}",
            code="OPENAI_SERVICE_ERROR"
        )
        self.operation = operation
        self.reason = reason


class ValidationError(RAGAPIException):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, reason: str):
        """Initialize with field name and validation reason.
        
        Args:
            field: The field that failed validation
            reason: Reason for the validation failure
        """
        super().__init__(
            message=f"Validation error for field '{field}': {reason}",
            code="VALIDATION_ERROR"
        )
        self.field = field
        self.reason = reason
