"""Integration tests for health check endpoint.

Tests Requirements: 1.1, 1.2, 1.3
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(test_client: AsyncClient):
    """Test that health endpoint returns 200 OK status.
    
    Requirement 1.2: WHEN a GET request is received at "/health", 
    THE RAG_API_Server SHALL return HTTP status code 200
    """
    response = await test_client.get("/health")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_returns_correct_structure(test_client: AsyncClient):
    """Test that health endpoint returns correct JSON structure.
    
    Requirement 1.3: WHEN a GET request is received at "/health", 
    THE RAG_API_Server SHALL return a JSON response containing fields 
    "status" with value "ok" and "version" with the current service version
    """
    response = await test_client.get("/health")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert data["status"] == "ok"
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


@pytest.mark.asyncio
async def test_health_endpoint_accessible(test_client: AsyncClient):
    """Test that health endpoint is accessible at /health path.
    
    Requirement 1.1: THE RAG_API_Server SHALL expose a GET endpoint at path "/health"
    """
    response = await test_client.get("/health")
    
    # Should not return 404
    assert response.status_code != 404
    assert response.status_code == 200
