"""Database models for sessions, messages, and documents."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    """Valid message roles matching database CHECK constraint."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Session(BaseModel):
    """Session model representing a conversation thread."""
    id: str
    user_id: Optional[str] = None
    created_at: datetime
    last_active_at: datetime

    class Config:
        from_attributes = True


class Message(BaseModel):
    """Message model representing a single turn in a conversation."""
    id: int
    session_id: str
    role: MessageRole
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentInfo(BaseModel):
    """Document metadata model."""
    id: str
    title: Optional[str] = None
    source: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
