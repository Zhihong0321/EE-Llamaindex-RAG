"""Data models for the RAG API."""

from app.models.database import Session, Message, MessageRole, DocumentInfo
from app.models.requests import IngestRequest, ChatRequest, ChatConfig
from app.models.responses import (
    HealthResponse,
    IngestResponse,
    ChatResponse,
    Source,
    DocumentsResponse,
)

__all__ = [
    # Database models
    "Session",
    "Message",
    "MessageRole",
    "DocumentInfo",
    # Request models
    "IngestRequest",
    "ChatRequest",
    "ChatConfig",
    # Response models
    "HealthResponse",
    "IngestResponse",
    "ChatResponse",
    "Source",
    "DocumentsResponse",
]
