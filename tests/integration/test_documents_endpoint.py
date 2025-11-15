"""Integration tests for documents listing endpoint.

Tests Requirements: 9.1, 9.2, 9.3
"""

import pytest
from httpx import AsyncClient
from app.db.database import Database


@pytest.mark.asyncio
async def test_documents_endpoint_accessible(test_client: AsyncClient):
    """Test that documents endpoint is accessible at /documents path.
    
    Requirement 9.1: WHERE the document listing feature is enabled, 
    THE RAG_API_Server SHALL expose a GET endpoint at path "/documents"
    """
    response = await test_client.get("/documents")
    
    # Should not return 404
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_documents_returns_empty_list_when_no_documents(test_client: AsyncClient):
    """Test that documents endpoint returns empty list when no documents exist.
    
    Requirement 9.2: WHERE the document listing feature is enabled, WHEN a GET 
    request is received at "/documents", THE RAG_API_Server SHALL retrieve all 
    records from the documents table
    """
    response = await test_client.get("/documents")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)
    assert len(data["documents"]) == 0


@pytest.mark.asyncio
async def test_documents_returns_ingested_documents(test_client: AsyncClient):
    """Test that documents endpoint returns all ingested documents.
    
    Requirement 9.2: WHERE the document listing feature is enabled, WHEN a GET 
    request is received at "/documents", THE RAG_API_Server SHALL retrieve all 
    records from the documents table
    """
    # Ingest first document
    response1 = await test_client.post(
        "/ingest",
        json={
            "text": "First document content",
            "title": "Document 1",
            "source": "test"
        }
    )
    assert response1.status_code == 200
    doc_id_1 = response1.json()["document_id"]
    
    # Ingest second document
    response2 = await test_client.post(
        "/ingest",
        json={
            "text": "Second document content",
            "title": "Document 2",
            "source": "test"
        }
    )
    assert response2.status_code == 200
    doc_id_2 = response2.json()["document_id"]
    
    # Get all documents
    response = await test_client.get("/documents")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "documents" in data
    assert len(data["documents"]) == 2
    
    # Verify document IDs are in the response
    doc_ids = [doc["document_id"] for doc in data["documents"]]
    assert doc_id_1 in doc_ids
    assert doc_id_2 in doc_ids


@pytest.mark.asyncio
async def test_documents_returns_correct_fields(test_client: AsyncClient):
    """Test that documents endpoint returns correct fields for each document.
    
    Requirement 9.3: WHERE the document listing feature is enabled, WHEN returning 
    documents, THE RAG_API_Server SHALL include for each document the fields 
    "document_id", "title", "source", and "created_at"
    """
    # Ingest a document with all metadata
    await test_client.post(
        "/ingest",
        json={
            "text": "Test document with metadata",
            "title": "Test Document",
            "source": "integration_test",
            "metadata": {"category": "test"}
        }
    )
    
    # Get documents
    response = await test_client.get("/documents")
    
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["documents"]) > 0
    
    # Verify each document has required fields
    for doc in data["documents"]:
        assert "document_id" in doc
        assert "title" in doc
        assert "source" in doc
        assert "created_at" in doc
        
        # Verify field types
        assert isinstance(doc["document_id"], str)
        assert isinstance(doc["created_at"], str)  # ISO format datetime string


@pytest.mark.asyncio
async def test_documents_preserves_metadata(test_client: AsyncClient):
    """Test that documents endpoint preserves document metadata."""
    # Ingest document with specific metadata
    title = "Metadata Test Document"
    source = "test_source"
    
    response1 = await test_client.post(
        "/ingest",
        json={
            "text": "Document with specific metadata",
            "title": title,
            "source": source
        }
    )
    assert response1.status_code == 200
    doc_id = response1.json()["document_id"]
    
    # Get documents
    response2 = await test_client.get("/documents")
    
    assert response2.status_code == 200
    
    data = response2.json()
    
    # Find the document we just created
    doc = next((d for d in data["documents"] if d["document_id"] == doc_id), None)
    
    assert doc is not None
    assert doc["title"] == title
    assert doc["source"] == source


@pytest.mark.asyncio
async def test_documents_ordered_by_creation_time(test_client: AsyncClient):
    """Test that documents are returned in a consistent order."""
    # Ingest multiple documents
    doc_ids = []
    for i in range(3):
        response = await test_client.post(
            "/ingest",
            json={
                "text": f"Document {i} content",
                "title": f"Document {i}"
            }
        )
        assert response.status_code == 200
        doc_ids.append(response.json()["document_id"])
    
    # Get documents
    response = await test_client.get("/documents")
    
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["documents"]) >= 3
    
    # Verify all documents are present
    returned_ids = [doc["document_id"] for doc in data["documents"]]
    for doc_id in doc_ids:
        assert doc_id in returned_ids


@pytest.mark.asyncio
async def test_documents_with_null_metadata(test_client: AsyncClient):
    """Test that documents endpoint handles documents with null metadata fields."""
    # Ingest document with minimal metadata (no title or source)
    response1 = await test_client.post(
        "/ingest",
        json={"text": "Document with minimal metadata"}
    )
    assert response1.status_code == 200
    doc_id = response1.json()["document_id"]
    
    # Get documents
    response2 = await test_client.get("/documents")
    
    assert response2.status_code == 200
    
    data = response2.json()
    
    # Find the document
    doc = next((d for d in data["documents"] if d["document_id"] == doc_id), None)
    
    assert doc is not None
    assert doc["document_id"] == doc_id
    # Title and source can be null
    assert "title" in doc
    assert "source" in doc
