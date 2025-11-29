"""Request models for API endpoints."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any


class IngestRequest(BaseModel):
    """Request model for document ingestion endpoint."""
    text: str = Field(..., min_length=1, description="Document text content")
    title: Optional[str] = Field(None, description="Document title")
    source: Optional[str] = Field(None, description="Document source")
    vault_id: Optional[str] = Field(None, description="Vault ID for multi-tenancy isolation")
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
    vault_id: Optional[str] = Field(None, description="Vault ID for multi-tenancy filtering")
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


class VaultCreateRequest(BaseModel):
    """Request model for vault creation."""
    name: str = Field(..., min_length=1, description="Vault name")
    description: Optional[str] = Field(None, description="Vault description")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()


class AgentCreateRequest(BaseModel):
    """Request model for agent creation."""
    name: str = Field(..., min_length=1, description="Agent name")
    vault_id: str = Field(..., min_length=1, description="Associated vault ID")
    system_prompt: str = Field(..., min_length=1, description="System prompt for the agent")

    @field_validator("name", "vault_id", "system_prompt")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure fields are not just whitespace."""
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()
