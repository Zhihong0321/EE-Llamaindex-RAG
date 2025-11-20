"""Response models for API endpoints."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")


class IngestResponse(BaseModel):
    """Response model for document ingestion endpoint."""
    document_id: str = Field(..., description="Unique document identifier")
    status: str = Field(..., description="Ingestion status")


class DeleteResponse(BaseModel):
    """Response model for document deletion endpoint."""
    document_id: str = Field(..., description="Unique document identifier")
    status: str = Field(..., description="Deletion status")


class Source(BaseModel):
    """Source information for retrieved document chunks."""
    document_id: str = Field(..., description="Document identifier")
    title: Optional[str] = Field(None, description="Document title")
    snippet: str = Field(..., description="Text snippet from document")
    score: float = Field(..., description="Relevance score")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    session_id: str = Field(..., description="Session identifier")
    answer: str = Field(..., description="Generated response")
    sources: List[Source] = Field(
        default_factory=list,
        description="Retrieved source documents"
    )


class DocumentInfo(BaseModel):
    """Document information for listing endpoint."""
    document_id: str = Field(..., description="Document identifier")
    title: Optional[str] = Field(None, description="Document title")
    source: Optional[str] = Field(None, description="Document source")
    created_at: datetime = Field(..., description="Creation timestamp")


class DocumentsResponse(BaseModel):
    """Response model for documents listing endpoint."""
    documents: List[DocumentInfo] = Field(
        default_factory=list,
        description="List of documents"
    )
