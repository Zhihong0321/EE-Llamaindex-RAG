"""Agent management API endpoints.

This module provides CRUD operations for agents:
- POST /agents - Create new agent
- GET /agents - List all agents (with optional vault_id filter)
- GET /agents/{agent_id} - Get single agent
- DELETE /agents/{agent_id} - Delete agent
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional

from app.models.requests import AgentCreateRequest
from app.models.responses import AgentResponse, AgentDeleteResponse
from app.services.agent_service import AgentService, AgentNotFoundError
from app.logging_config import get_logger


logger = get_logger(__name__)
router = APIRouter()

# Service will be injected at startup
_agent_service: AgentService = None


def set_agent_service(agent_service: AgentService):
    """Inject agent service dependency.
    
    Args:
        agent_service: AgentService instance
    """
    global _agent_service
    _agent_service = agent_service


@router.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Create a new agent",
    description="Create a new AI agent configuration associated with a vault."
)
async def create_agent(request: AgentCreateRequest):
    """Create a new agent.
    
    Args:
        request: Agent creation request with name, vault_id, and system_prompt
        
    Returns:
        AgentResponse: Created agent with metadata
        
    Raises:
        HTTPException 500: If creation fails
    """
    logger.info("POST /agents", extra={"agent_name": request.name})
    
    try:
        agent = await _agent_service.create(
            name=request.name,
            vault_id=request.vault_id,
            system_prompt=request.system_prompt
        )
        
        return AgentResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            vault_id=agent.vault_id,
            system_prompt=agent.system_prompt,
            created_at=agent.created_at
        )
        
    except Exception as e:
        logger.error(f"Agent creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent"
        )


@router.get(
    "/agents",
    response_model=List[AgentResponse],
    summary="List all agents",
    description="Retrieve all agents, optionally filtered by vault_id."
)
async def list_agents(vault_id: Optional[str] = Query(None, description="Filter by vault ID")):
    """List all agents.
    
    Args:
        vault_id: Optional vault ID to filter agents
    
    Returns:
        List[AgentResponse]: List of all agents
        
    Raises:
        HTTPException 500: If listing fails
    """
    logger.info("GET /agents", extra={"vault_id": vault_id})
    
    try:
        agents = await _agent_service.list_all(vault_id=vault_id)
        
        return [
            AgentResponse(
                agent_id=agent.agent_id,
                name=agent.name,
                vault_id=agent.vault_id,
                system_prompt=agent.system_prompt,
                created_at=agent.created_at
            )
            for agent in agents
        ]
        
    except Exception as e:
        logger.error(f"Agent listing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agents"
        )


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="Get agent by ID",
    description="Retrieve a single agent by its ID."
)
async def get_agent(agent_id: str):
    """Get agent by ID.
    
    Args:
        agent_id: Unique agent identifier
        
    Returns:
        AgentResponse: Agent with metadata
        
    Raises:
        HTTPException 404: If agent not found
        HTTPException 500: If retrieval fails
    """
    logger.info("GET /agents/{agent_id}", extra={"agent_id": agent_id})
    
    try:
        agent = await _agent_service.get_by_id(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        
        return AgentResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            vault_id=agent.vault_id,
            system_prompt=agent.system_prompt,
            created_at=agent.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent"
        )


@router.delete(
    "/agents/{agent_id}",
    response_model=AgentDeleteResponse,
    summary="Delete agent",
    description="Delete an agent configuration."
)
async def delete_agent(agent_id: str):
    """Delete agent.
    
    Args:
        agent_id: Unique agent identifier
        
    Returns:
        AgentDeleteResponse: Deletion confirmation
        
    Raises:
        HTTPException 404: If agent not found
        HTTPException 500: If deletion fails
    """
    logger.info("DELETE /agents/{agent_id}", extra={"agent_id": agent_id})
    
    try:
        await _agent_service.delete(agent_id)
        
        return AgentDeleteResponse(
            success=True,
            message="Agent deleted successfully"
        )
        
    except AgentNotFoundError as e:
        logger.warning(f"Agent deletion failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Agent deletion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
        )
