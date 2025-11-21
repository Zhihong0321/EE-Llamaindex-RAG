"""Vault service for managing document vaults.

This service handles:
- Vault creation with unique name validation
- Vault listing and retrieval
- Vault deletion with cascade to documents
- Vault existence validation
"""

import uuid
from datetime import datetime
from typing import List, Optional

from app.db.database import Database
from app.models.database import Vault
from app.logging_config import get_logger
from app.exceptions import RAGAPIException


logger = get_logger(__name__)


class VaultNotFoundError(RAGAPIException):
    """Exception raised when vault is not found."""
    
    def __init__(self, vault_id: str):
        self.vault_id = vault_id
        super().__init__(
            code="VAULT_NOT_FOUND",
            message=f"Vault not found: {vault_id}"
        )


class VaultAlreadyExistsError(RAGAPIException):
    """Exception raised when vault name already exists."""
    
    def __init__(self, name: str):
        self.name = name
        super().__init__(
            code="VAULT_ALREADY_EXISTS",
            message=f"Vault with name '{name}' already exists"
        )


class VaultService:
    """Service for vault management."""
    
    def __init__(self, db: Database):
        """Initialize VaultService.
        
        Args:
            db: Database instance for vault storage
        """
        self.db = db
    
    async def create(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Vault:
        """Create a new vault.
        
        Args:
            name: Vault name (must be unique)
            description: Optional vault description
            
        Returns:
            Vault: Created vault object
            
        Raises:
            VaultAlreadyExistsError: If vault with same name exists
        """
        logger.info("Creating vault", extra={"name": name})
        
        # Check if vault with same name already exists (case-insensitive)
        existing = await self.get_by_name(name)
        if existing:
            logger.warning(
                "Vault creation failed: name already exists",
                extra={"name": name}
            )
            raise VaultAlreadyExistsError(name)
        
        # Generate unique vault_id
        vault_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        try:
            query = """
                INSERT INTO vaults (vault_id, name, description, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING vault_id, name, description, created_at, updated_at
            """
            
            row = await self.db.fetchrow(
                query,
                vault_id,
                name,
                description,
                now,
                now
            )
            
            vault = Vault(
                vault_id=row["vault_id"],
                name=row["name"],
                description=row["description"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            
            logger.info(
                "Vault created successfully",
                extra={"vault_id": vault_id, "name": name}
            )
            
            return vault
            
        except Exception as e:
            logger.error(
                "Vault creation failed",
                extra={"name": name, "error": str(e)},
                exc_info=True
            )
            raise
    
    async def list_all(self) -> List[Vault]:
        """Retrieve all vaults.
        
        Returns:
            List[Vault]: List of all vaults
        """
        logger.debug("Listing all vaults")
        
        query = """
            SELECT vault_id, name, description, created_at, updated_at
            FROM vaults
            ORDER BY created_at DESC
        """
        
        rows = await self.db.fetch(query)
        
        vaults = [
            Vault(
                vault_id=row["vault_id"],
                name=row["name"],
                description=row["description"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]
        
        logger.info(f"Retrieved {len(vaults)} vaults")
        
        return vaults
    
    async def get_by_id(self, vault_id: str) -> Optional[Vault]:
        """Retrieve vault by ID.
        
        Args:
            vault_id: Unique vault identifier
            
        Returns:
            Optional[Vault]: Vault object or None if not found
        """
        logger.debug("Retrieving vault by ID", extra={"vault_id": vault_id})
        
        query = """
            SELECT vault_id, name, description, created_at, updated_at
            FROM vaults
            WHERE vault_id = $1
        """
        
        row = await self.db.fetchrow(query, vault_id)
        
        if row is None:
            logger.warning("Vault not found", extra={"vault_id": vault_id})
            return None
        
        vault = Vault(
            vault_id=row["vault_id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
        
        logger.info("Vault retrieved", extra={"vault_id": vault_id})
        
        return vault
    
    async def get_by_name(self, name: str) -> Optional[Vault]:
        """Retrieve vault by name (case-insensitive).
        
        Args:
            name: Vault name
            
        Returns:
            Optional[Vault]: Vault object or None if not found
        """
        logger.debug("Retrieving vault by name", extra={"name": name})
        
        query = """
            SELECT vault_id, name, description, created_at, updated_at
            FROM vaults
            WHERE LOWER(name) = LOWER($1)
        """
        
        row = await self.db.fetchrow(query, name)
        
        if row is None:
            return None
        
        return Vault(
            vault_id=row["vault_id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    async def count_documents(self, vault_id: str) -> int:
        """Count documents in a vault.
        
        Args:
            vault_id: Unique vault identifier
            
        Returns:
            int: Number of documents in vault
        """
        query = """
            SELECT COUNT(*) as count
            FROM documents
            WHERE vault_id = $1
        """
        
        count = await self.db.fetchval(query, vault_id)
        
        return count or 0
    
    async def delete(self, vault_id: str) -> None:
        """Delete vault and all associated documents (cascade).
        
        Args:
            vault_id: Unique vault identifier
            
        Raises:
            VaultNotFoundError: If vault does not exist
        """
        logger.info("Deleting vault", extra={"vault_id": vault_id})
        
        # Check if vault exists
        vault = await self.get_by_id(vault_id)
        if not vault:
            raise VaultNotFoundError(vault_id)
        
        try:
            # Delete vault (CASCADE will delete associated documents)
            query = "DELETE FROM vaults WHERE vault_id = $1"
            await self.db.execute(query, vault_id)
            
            logger.info(
                "Vault deleted successfully",
                extra={"vault_id": vault_id}
            )
            
        except Exception as e:
            logger.error(
                "Vault deletion failed",
                extra={"vault_id": vault_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    async def validate_exists(self, vault_id: str) -> None:
        """Validate that a vault exists.
        
        Args:
            vault_id: Unique vault identifier
            
        Raises:
            VaultNotFoundError: If vault does not exist
        """
        vault = await self.get_by_id(vault_id)
        if not vault:
            raise VaultNotFoundError(vault_id)
