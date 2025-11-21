"""Unit tests for VaultService."""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.database import Vault


@pytest.fixture
def mock_db():
    """Create mock database."""
    return AsyncMock()


@pytest.fixture
def vault_service(mock_db):
    """Create VaultService with mock database."""
    # Import here to avoid circular import
    from app.services.vault_service import VaultService
    return VaultService(mock_db)


@pytest.mark.asyncio
async def test_create_vault_success(vault_service, mock_db):
    """Test successful vault creation."""
    # Mock get_by_name to return None (vault doesn't exist)
    vault_service.get_by_name = AsyncMock(return_value=None)
    
    # Mock database response
    mock_row = {
        "vault_id": "test-vault-id",
        "name": "Test Vault",
        "description": "Test description",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    mock_db.fetchrow.return_value = mock_row
    
    # Create vault
    vault = await vault_service.create(
        name="Test Vault",
        description="Test description"
    )
    
    # Assertions
    assert vault.name == "Test Vault"
    assert vault.description == "Test description"
    assert mock_db.fetchrow.called


@pytest.mark.asyncio
async def test_create_vault_duplicate_name(vault_service, mock_db):
    """Test vault creation with duplicate name."""
    from app.services.vault_service import VaultAlreadyExistsError
    
    # Mock get_by_name to return existing vault
    existing_vault = Vault(
        vault_id="existing-id",
        name="Test Vault",
        description="Existing",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    vault_service.get_by_name = AsyncMock(return_value=existing_vault)
    
    # Attempt to create vault with same name
    with pytest.raises(VaultAlreadyExistsError) as exc_info:
        await vault_service.create(name="Test Vault")
    
    assert exc_info.value.name == "Test Vault"
    assert exc_info.value.code == "VAULT_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_list_all_vaults(vault_service, mock_db):
    """Test listing all vaults."""
    # Mock database response
    mock_rows = [
        {
            "vault_id": "vault-1",
            "name": "Vault 1",
            "description": "First vault",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "vault_id": "vault-2",
            "name": "Vault 2",
            "description": "Second vault",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    mock_db.fetch.return_value = mock_rows
    
    # List vaults
    vaults = await vault_service.list_all()
    
    # Assertions
    assert len(vaults) == 2
    assert vaults[0].name == "Vault 1"
    assert vaults[1].name == "Vault 2"
    assert mock_db.fetch.called


@pytest.mark.asyncio
async def test_get_vault_by_id_found(vault_service, mock_db):
    """Test getting vault by ID when it exists."""
    # Mock database response
    mock_row = {
        "vault_id": "test-vault-id",
        "name": "Test Vault",
        "description": "Test description",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    mock_db.fetchrow.return_value = mock_row
    
    # Get vault
    vault = await vault_service.get_by_id("test-vault-id")
    
    # Assertions
    assert vault is not None
    assert vault.vault_id == "test-vault-id"
    assert vault.name == "Test Vault"


@pytest.mark.asyncio
async def test_get_vault_by_id_not_found(vault_service, mock_db):
    """Test getting vault by ID when it doesn't exist."""
    # Mock database response
    mock_db.fetchrow.return_value = None
    
    # Get vault
    vault = await vault_service.get_by_id("nonexistent-id")
    
    # Assertions
    assert vault is None


@pytest.mark.asyncio
async def test_get_vault_by_name_case_insensitive(vault_service, mock_db):
    """Test getting vault by name is case-insensitive."""
    # Mock database response
    mock_row = {
        "vault_id": "test-vault-id",
        "name": "Test Vault",
        "description": "Test description",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    mock_db.fetchrow.return_value = mock_row
    
    # Get vault with different case
    vault = await vault_service.get_by_name("test vault")
    
    # Assertions
    assert vault is not None
    assert vault.name == "Test Vault"


@pytest.mark.asyncio
async def test_count_documents(vault_service, mock_db):
    """Test counting documents in a vault."""
    # Mock database response
    mock_db.fetchval.return_value = 5
    
    # Count documents
    count = await vault_service.count_documents("test-vault-id")
    
    # Assertions
    assert count == 5
    assert mock_db.fetchval.called


@pytest.mark.asyncio
async def test_count_documents_empty(vault_service, mock_db):
    """Test counting documents in empty vault."""
    # Mock database response
    mock_db.fetchval.return_value = None
    
    # Count documents
    count = await vault_service.count_documents("test-vault-id")
    
    # Assertions
    assert count == 0


@pytest.mark.asyncio
async def test_delete_vault_success(vault_service, mock_db):
    """Test successful vault deletion."""
    # Mock get_by_id to return vault
    mock_vault = Vault(
        vault_id="test-vault-id",
        name="Test Vault",
        description="Test",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    vault_service.get_by_id = AsyncMock(return_value=mock_vault)
    
    # Delete vault
    await vault_service.delete("test-vault-id")
    
    # Assertions
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_delete_vault_not_found(vault_service, mock_db):
    """Test deleting non-existent vault."""
    from app.services.vault_service import VaultNotFoundError
    
    # Mock get_by_id to return None
    vault_service.get_by_id = AsyncMock(return_value=None)
    
    # Attempt to delete vault
    with pytest.raises(VaultNotFoundError) as exc_info:
        await vault_service.delete("nonexistent-id")
    
    assert exc_info.value.vault_id == "nonexistent-id"
    assert exc_info.value.code == "VAULT_NOT_FOUND"


@pytest.mark.asyncio
async def test_validate_exists_success(vault_service, mock_db):
    """Test validating vault exists."""
    # Mock get_by_id to return vault
    mock_vault = Vault(
        vault_id="test-vault-id",
        name="Test Vault",
        description="Test",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    vault_service.get_by_id = AsyncMock(return_value=mock_vault)
    
    # Validate vault exists (should not raise)
    await vault_service.validate_exists("test-vault-id")


@pytest.mark.asyncio
async def test_validate_exists_not_found(vault_service, mock_db):
    """Test validating non-existent vault."""
    from app.services.vault_service import VaultNotFoundError
    
    # Mock get_by_id to return None
    vault_service.get_by_id = AsyncMock(return_value=None)
    
    # Validate vault exists
    with pytest.raises(VaultNotFoundError):
        await vault_service.validate_exists("nonexistent-id")
