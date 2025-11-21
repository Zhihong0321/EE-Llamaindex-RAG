"""Integration tests for vault endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_vault(client: AsyncClient):
    """Test creating a new vault."""
    response = await client.post(
        "/vaults",
        json={
            "name": "Test Vault",
            "description": "A test vault for documents"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "vault_id" in data
    assert data["name"] == "Test Vault"
    assert data["description"] == "A test vault for documents"
    assert data["document_count"] == 0
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_vault_duplicate_name(client: AsyncClient):
    """Test creating vault with duplicate name."""
    # Create first vault
    response1 = await client.post(
        "/vaults",
        json={"name": "Duplicate Vault"}
    )
    assert response1.status_code == 201
    
    # Try to create vault with same name
    response2 = await client.post(
        "/vaults",
        json={"name": "Duplicate Vault"}
    )
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_vault_missing_name(client: AsyncClient):
    """Test creating vault without name."""
    response = await client.post(
        "/vaults",
        json={"description": "No name provided"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_vault_empty_name(client: AsyncClient):
    """Test creating vault with empty name."""
    response = await client.post(
        "/vaults",
        json={"name": "   "}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_vaults_empty(client: AsyncClient):
    """Test listing vaults when none exist."""
    response = await client.get("/vaults")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_vaults_with_data(client: AsyncClient):
    """Test listing vaults with data."""
    # Create multiple vaults
    vault1 = await client.post(
        "/vaults",
        json={"name": "Vault 1", "description": "First vault"}
    )
    vault2 = await client.post(
        "/vaults",
        json={"name": "Vault 2", "description": "Second vault"}
    )
    
    assert vault1.status_code == 201
    assert vault2.status_code == 201
    
    # List vaults
    response = await client.get("/vaults")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    
    # Check that our vaults are in the list
    vault_names = [v["name"] for v in data]
    assert "Vault 1" in vault_names
    assert "Vault 2" in vault_names


@pytest.mark.asyncio
async def test_get_vault_by_id(client: AsyncClient):
    """Test getting a specific vault by ID."""
    # Create vault
    create_response = await client.post(
        "/vaults",
        json={"name": "Get Test Vault", "description": "Test description"}
    )
    assert create_response.status_code == 201
    vault_id = create_response.json()["vault_id"]
    
    # Get vault by ID
    response = await client.get(f"/vaults/{vault_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["vault_id"] == vault_id
    assert data["name"] == "Get Test Vault"
    assert data["description"] == "Test description"
    assert data["document_count"] == 0


@pytest.mark.asyncio
async def test_get_vault_not_found(client: AsyncClient):
    """Test getting non-existent vault."""
    response = await client.get("/vaults/nonexistent-vault-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_vault(client: AsyncClient):
    """Test deleting a vault."""
    # Create vault
    create_response = await client.post(
        "/vaults",
        json={"name": "Delete Test Vault"}
    )
    assert create_response.status_code == 201
    vault_id = create_response.json()["vault_id"]
    
    # Delete vault
    delete_response = await client.delete(f"/vaults/{vault_id}")
    
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["vault_id"] == vault_id
    assert data["status"] == "deleted"
    
    # Verify vault is deleted
    get_response = await client.get(f"/vaults/{vault_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_vault_not_found(client: AsyncClient):
    """Test deleting non-existent vault."""
    response = await client.delete("/vaults/nonexistent-vault-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_vault_with_documents(client: AsyncClient):
    """Test vault document count with documents."""
    # Create vault
    vault_response = await client.post(
        "/vaults",
        json={"name": "Vault with Docs"}
    )
    assert vault_response.status_code == 201
    vault_id = vault_response.json()["vault_id"]
    
    # Ingest document into vault
    doc_response = await client.post(
        "/ingest",
        json={
            "text": "This is a test document in a vault.",
            "title": "Test Doc",
            "vault_id": vault_id
        }
    )
    assert doc_response.status_code == 200
    
    # Get vault and check document count
    get_response = await client.get(f"/vaults/{vault_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["document_count"] == 1


@pytest.mark.asyncio
async def test_delete_vault_cascades_documents(client: AsyncClient):
    """Test that deleting vault also deletes its documents."""
    # Create vault
    vault_response = await client.post(
        "/vaults",
        json={"name": "Cascade Test Vault"}
    )
    assert vault_response.status_code == 201
    vault_id = vault_response.json()["vault_id"]
    
    # Ingest document into vault
    doc_response = await client.post(
        "/ingest",
        json={
            "text": "Document to be cascaded.",
            "title": "Cascade Doc",
            "vault_id": vault_id
        }
    )
    assert doc_response.status_code == 200
    document_id = doc_response.json()["document_id"]
    
    # Delete vault
    delete_response = await client.delete(f"/vaults/{vault_id}")
    assert delete_response.status_code == 200
    
    # Verify document is also deleted
    # List documents filtered by vault_id should return empty
    docs_response = await client.get(f"/documents?vault_id={vault_id}")
    assert docs_response.status_code == 200
    assert len(docs_response.json()["documents"]) == 0
