"""Documents listing endpoint for knowledge management.

This module implements the optional documents listing endpoint as specified 
in Requirement 9.
"""

from fastapi import APIRouter, HTTPException, status

from app.models.responses import DocumentsResponse, DocumentInfo
from app.services.document_service import DocumentService


router = APIRouter()

# This will be injected via dependency injection in main.py
document_service: DocumentService = None


def set_document_service(service: DocumentService) -> None:
    """Set the document service instance.
    
    Args:
        service: DocumentService instance to use for listing documents
    """
    global document_service
    document_service = service


@router.get("/documents", response_model=DocumentsResponse, status_code=status.HTTP_200_OK)
async def list_documents() -> DocumentsResponse:
    """List all ingested documents.
    
    Returns all documents that have been ingested into the system with their
    metadata including document_id, title, source, and created_at timestamp.
    
    Requirements:
    - 9.1: WHERE the document listing feature is enabled, THE RAG_API_Server 
           SHALL expose a GET endpoint at path "/documents"
    - 9.2: WHERE the document listing feature is enabled, WHEN a GET request 
           is received at "/documents", THE RAG_API_Server SHALL retrieve all 
           records from the documents table
    - 9.3: WHERE the document listing feature is enabled, WHEN returning 
           documents, THE RAG_API_Server SHALL include for each document the 
           fields "document_id", "title", "source", and "created_at"
    
    Returns:
        DocumentsResponse: List of all documents with metadata
        
    Raises:
        HTTPException: 500 if document service not initialized or retrieval fails
    """
    if document_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document service not initialized"
        )
    
    try:
        # Retrieve all documents from database (Requirement 9.2)
        documents = await document_service.list_all()
        
        # Convert to response format with required fields (Requirement 9.3)
        document_infos = [
            DocumentInfo(
                document_id=doc.id,
                title=doc.title,
                source=doc.source,
                created_at=doc.created_at
            )
            for doc in documents
        ]
        
        return DocumentsResponse(documents=document_infos)
        
    except Exception as e:
        # Error handling for document retrieval failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )
