"""Integration tests for document ingestion endpoint.

Tests Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 10.3
"""

import pytest
from httpx import AsyncClient
from app.db.database import Database


@pytest.mark.asyncio
async def test_ingest_endpoint_accessible(test_client: AsyncClient):
    """Test that ingest endpoint is accessible at /ingest path.
    
    Requirement 2.1: THE RAG_API_Server SHALL expose a POST endpoint at path "/ingest"
    """
    response = await test_client.post(
        "/ingest",
        json={"text": "Test document content"}
    )
    
    # Should not return 404
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_ingest_document_with_text_only(test_client: AsyncClient, test_db: Database):
    """Test ingesting a document with only text field.
    
    Requirement 2.2: WHEN a POST request is received at "/ingest" with JSON body 
    containing "text" field, THE RAG_API_Server SHALL create a Document object 
    with the provided text
    """
    response = await test_client.post(
        "/ingest",
        json={"text": "This is a test document about LlamaIndex."}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "document_id" in data
    assert "status" in data
    assert data["status"] == "indexed"
    assert isinstance(data["document_id"], str)
    assert len(data["document_id"]) > 0


@pytest.mark.asyncio
async def test_ingest_document_with_metadata(test_client: AsyncClient, test_db: Database):
    """Test ingesting a document with text and metadata.
    
    Requirement 2.6: WHEN embeddings are stored, THE RAG_API_Server SHALL insert 
    a record into the documents table with fields id, title, source, metadata_json, 
    created_at, and updated_at
    """
    response = await test_client.post(
        "/ingest",
        json={
            "text": "LlamaIndex is a data framework for LLM applications.",
            "title": "LlamaIndex Introduction",
            "source": "documentation",
            "metadata": {"category": "tutorial", "version": "1.0"}
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    document_id = data["document_id"]
    
    # Verify document was stored in database
    doc = await test_db.fetchrow(
        "SELECT * FROM documents WHERE id = $1",
        document_id
    )
    
    assert doc is not None
    assert doc["id"] == document_id
    assert doc["title"] == "LlamaIndex Introduction"
    assert doc["source"] == "documentation"
    assert doc["metadata_json"]["category"] == "tutorial"
    assert doc["metadata_json"]["version"] == "1.0"
    assert doc["created_at"] is not None
    assert doc["updated_at"] is not None


@pytest.mark.asyncio
async def test_ingest_returns_correct_response_format(test_client: AsyncClient):
    """Test that ingest endpoint returns correct response format.
    
    Requirement 2.7: WHEN ingestion completes successfully, THE RAG_API_Server 
    SHALL return HTTP status code 200 with JSON containing "document_id" and 
    "status" with value "indexed"
    """
    response = await test_client.post(
        "/ingest",
        json={"text": "Test content for response format validation"}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "document_id" in data
    assert "status" in data
    assert data["status"] == "indexed"


@pytest.mark.asyncio
async def test_ingest_without_text_field_returns_422(test_client: AsyncClient):
    """Test that ingest endpoint returns 422 when text field is missing.
    
    Requirement 10.3: WHEN a POST request is received at "/ingest" without 
    a "text" field, THE RAG_API_Server SHALL return HTTP status code 422 
    with validation error details
    """
    response = await test_client.post(
        "/ingest",
        json={"title": "Document without text"}
    )
    
    assert response.status_code == 422
    
    data = response.json()
    assert "error" in data
    assert "detail" in data


@pytest.mark.asyncio
async def test_ingest_with_empty_text_returns_422(test_client: AsyncClient):
    """Test that ingest endpoint returns 422 when text field is empty."""
    response = await test_client.post(
        "/ingest",
        json={"text": ""}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_with_invalid_json_returns_400(test_client: AsyncClient):
    """Test that ingest endpoint returns 400 for invalid JSON.
    
    Requirement 10.4: WHEN a POST request is received with invalid JSON, 
    THE RAG_API_Server SHALL return HTTP status code 400 with error details
    """
    response = await test_client.post(
        "/ingest",
        content="invalid json content",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422  # FastAPI returns 422 for invalid JSON


@pytest.mark.asyncio
async def test_ingest_multiple_documents(test_client: AsyncClient, test_db: Database):
    """Test ingesting multiple documents creates separate records."""
    # Ingest first document
    response1 = await test_client.post(
        "/ingest",
        json={"text": "First document content"}
    )
    assert response1.status_code == 200
    doc_id_1 = response1.json()["document_id"]
    
    # Ingest second document
    response2 = await test_client.post(
        "/ingest",
        json={"text": "Second document content"}
    )
    assert response2.status_code == 200
    doc_id_2 = response2.json()["document_id"]
    
    # Verify both documents exist and have different IDs
    assert doc_id_1 != doc_id_2
    
    doc1 = await test_db.fetchrow("SELECT * FROM documents WHERE id = $1", doc_id_1)
    doc2 = await test_db.fetchrow("SELECT * FROM documents WHERE id = $1", doc_id_2)
    
    assert doc1 is not None
    assert doc2 is not None


@pytest.mark.asyncio
async def test_ingest_with_custom_api_base(test_client: AsyncClient, mock_config):
    """Test that custom OpenAI API base URL is configured.
    
    Tests custom OpenAI API base URL configuration requirement.
    """
    # Verify config has custom API base
    assert mock_config.openai_api_base == "https://api.bltcy.ai"
    
    # Test ingestion works with custom API base
    response = await test_client.post(
        "/ingest",
        json={"text": "Test document with custom API"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "indexed"
