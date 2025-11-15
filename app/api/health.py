"""Health check endpoint for service monitoring.

This module implements the health check endpoint as specified in Requirement 1.
"""

from fastapi import APIRouter, Depends
from app.models.responses import HealthResponse
from app.config import Config, get_config

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(config: Config = Depends(get_config)) -> HealthResponse:
    """Health check endpoint.
    
    Returns service status and version for monitoring and readiness checks.
    
    Requirements:
    - 1.1: THE RAG_API_Server SHALL expose a GET endpoint at path "/health"
    - 1.2: WHEN a GET request is received at "/health", THE RAG_API_Server 
           SHALL return HTTP status code 200
    - 1.3: WHEN a GET request is received at "/health", THE RAG_API_Server 
           SHALL return a JSON response containing fields "status" with value 
           "ok" and "version" with the current service version
    
    Args:
        config: Application configuration (injected via dependency)
    
    Returns:
        HealthResponse: Status and version information
    """
    return HealthResponse(
        status="ok",
        version=config.version
    )
