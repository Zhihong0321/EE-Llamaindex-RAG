"""Request models for API endpoints."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any


class IngestRequest(BaseModel):
    """Request model for document ingestion endpoint."""
    text: str = Field(..., min_length=1, description="Document text content")
    title: Optional[str] = Field(None, description="Document title")
    source: Optional[str] = Field(None, description="Document source")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v


class ChatConfig(BaseModel):
    """Configuration for chat request."""
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of document chunks to retrieve"
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation"
    )


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    session_id: str = Field(..., min_length=1, description="Session identifier")
    message: str = Field(..., min_length=1, description="User message")
    config: Optional[ChatConfig] = Field(
        default_factory=ChatConfig,
        description="Optional chat configuration"
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id_not_empty(cls, v: str) -> str:
        """Ensure session_id is not just whitespace."""
        if not v.strip():
            raise ValueError("Session ID cannot be empty or whitespace only")
        return v

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        """Ensure message is not just whitespace."""
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v
