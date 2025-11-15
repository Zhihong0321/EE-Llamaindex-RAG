"""Ingest endpoint for document ingestion.

This module implements the POST /ingest endpoint for ingesting documents
into the RAG system (Requirements 2.1-2.7, 10.3).
"""

import uuid
from fastapi import APIRouter, HTTPException, status

from app.models.requests import IngestRequest
from app.models.responses import IngestResponse
from app.services.document_service import DocumentService


router = APIRouter()

# This will be injected via dependency injection in main.py
document_service: DocumentService = None


def set_document_service(service: DocumentService) -> None:
    """Set the document service instance.
    
    Args:
        service: DocumentService instance to use for ingestion
    """
    global document_service
    document_service = service


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_200_OK)
async def ingest_document(request: IngestRequest) -> IngestResponse:
    """Ingest a document into the RAG system.
    
    Requirements:
    - 2.1: Expose POST endpoint at "/ingest"
    - 2.2: Create Document object with provided text
    - 2.3: Chunk text into segments suitable for embedding
    - 2.4: Generate embeddings using Embedding_Model
    - 2.5: Store embeddings in Vector_Store
    - 2.6: Insert record into documents table
    - 2.7: Return document_id and status "indexed"
    - 10.3: Validate required "text" field (handled by Pydantic)
    
    Args:
        request: IngestRequest containing text and optional metadata
        
    Returns:
        IngestResponse: Contains document_id and status
        
    Raises:
        HTTPException: 422 if validation fails (handled by FastAPI)
        HTTPException: 500 if ingestion fails
    """
    if document_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document service not initialized"
        )
    
    try:
        # Generate unique document_id using UUID
        document_id = str(uuid.uuid4())
        
        # Call DocumentService.ingest() with request data
        # This handles Requirements 2.2-2.6
        await document_service.ingest(
            document_id=document_id,
            text=request.text,
            title=request.title,
            source=request.source,
            metadata=request.metadata
        )
        
        # Return IngestResponse with document_id and status "indexed" (Requirement 2.7)
        return IngestResponse(
            document_id=document_id,
            status="indexed"
        )
        
    except Exception as e:
        # Error handling for ingestion failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )
