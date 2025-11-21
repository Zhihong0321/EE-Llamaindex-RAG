"""Vault management API endpoints.

This module provides CRUD operations for vaults:
- POST /vaults - Create new vault
- GET /vaults - List all vaults
- GET /vaults/{vault_id} - Get single vault
- DELETE /vaults/{vault_id} - Delete vault
"""

from fastapi import APIRouter, HTTPException, status, Response
from typing import List

from app.models.requests import VaultCreateRequest
from app.models.responses import VaultResponse, VaultDeleteResponse
from app.services.vault_service import VaultService, VaultNotFoundError, VaultAlreadyExistsError
from app.logging_config import get_logger


logger = get_logger(__name__)
router = APIRouter()


@router.options("/vaults")
@router.options("/vaults/{vault_id}")
async def options_handler(response: Response):
    """Handle CORS preflight requests."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"status": "ok"}

# Service will be injected at startup
_vault_service: VaultService = None


def set_vault_service(vault_service: VaultService):
    """Inject vault service dependency.
    
    Args:
        vault_service: VaultService instance
    """
    global _vault_service
    _vault_service = vault_service


@router.post(
    "/vaults",
    response_model=VaultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new vault",
    description="Create a new vault for organizing documents. Vault names must be unique.",
    responses={
        201: {"description": "Vault created successfully"},
        409: {"description": "Vault with same name already exists"},
    }
)
async def create_vault(request: VaultCreateRequest, response: Response):
    """Create a new vault.
    
    Args:
        request: Vault creation request with name and optional description
        
    Returns:
        VaultResponse: Created vault with metadata
        
    Raises:
        HTTPException 409: If vault with same name already exists
        HTTPException 500: If creation fails
    """
    logger.info("POST /vaults", extra={"name": request.name})
    
    # Add CORS headers explicitly
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        vault = await _vault_service.create(
            name=request.name,
            description=request.description
        )
        
        # Get document count (will be 0 for new vault)
        doc_count = await _vault_service.count_documents(vault.vault_id)
        
        return VaultResponse(
            vault_id=vault.vault_id,
            name=vault.name,
            description=vault.description,
            created_at=vault.created_at,
            document_count=doc_count
        )
        
    except VaultAlreadyExistsError as e:
        logger.warning(f"Vault creation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Vault creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vault"
        )


@router.get(
    "/vaults",
    response_model=List[VaultResponse],
    summary="List all vaults",
    description="Retrieve all vaults with document counts."
)
async def list_vaults(response: Response):
    """List all vaults.
    
    Returns:
        List[VaultResponse]: List of all vaults with metadata
        
    Raises:
        HTTPException 500: If listing fails
    """
    logger.info("GET /vaults")
    
    # Add CORS headers explicitly
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        vaults = await _vault_service.list_all()
        
        # Build response with document counts
        response = []
        for vault in vaults:
            doc_count = await _vault_service.count_documents(vault.vault_id)
            response.append(
                VaultResponse(
                    vault_id=vault.vault_id,
                    name=vault.name,
                    description=vault.description,
                    created_at=vault.created_at,
                    document_count=doc_count
                )
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Vault listing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list vaults"
        )


@router.get(
    "/vaults/{vault_id}",
    response_model=VaultResponse,
    summary="Get vault by ID",
    description="Retrieve a single vault by its ID with document count."
)
async def get_vault(vault_id: str, response: Response):
    """Get vault by ID.
    
    Args:
        vault_id: Unique vault identifier
        
    Returns:
        VaultResponse: Vault with metadata
        
    Raises:
        HTTPException 404: If vault not found
        HTTPException 500: If retrieval fails
    """
    logger.info("GET /vaults/{vault_id}", extra={"vault_id": vault_id})
    
    # Add CORS headers explicitly
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        vault = await _vault_service.get_by_id(vault_id)
        
        if not vault:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vault not found: {vault_id}"
            )
        
        doc_count = await _vault_service.count_documents(vault.vault_id)
        
        return VaultResponse(
            vault_id=vault.vault_id,
            name=vault.name,
            description=vault.description,
            created_at=vault.created_at,
            document_count=doc_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vault retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vault"
        )


@router.delete(
    "/vaults/{vault_id}",
    response_model=VaultDeleteResponse,
    summary="Delete vault",
    description="Delete a vault and all its associated documents (cascade delete)."
)
async def delete_vault(vault_id: str, response: Response):
    """Delete vault and all associated documents.
    
    Args:
        vault_id: Unique vault identifier
        
    Returns:
        VaultDeleteResponse: Deletion confirmation
        
    Raises:
        HTTPException 404: If vault not found
        HTTPException 500: If deletion fails
    """
    logger.info("DELETE /vaults/{vault_id}", extra={"vault_id": vault_id})
    
    # Add CORS headers explicitly
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        await _vault_service.delete(vault_id)
        
        return VaultDeleteResponse(
            vault_id=vault_id,
            status="deleted"
        )
        
    except VaultNotFoundError as e:
        logger.warning(f"Vault deletion failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Vault deletion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vault"
        )
