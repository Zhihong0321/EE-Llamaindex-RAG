"""Agent service for managing AI agents.

This service handles:
- Agent creation with vault association
- Agent listing and retrieval
- Agent filtering by vault
- Agent deletion
"""

import uuid
from datetime import datetime
from typing import List, Optional

from app.db.database import Database
from app.models.database import Agent
from app.logging_config import get_logger
from app.exceptions import RAGAPIException


logger = get_logger(__name__)


class AgentNotFoundError(RAGAPIException):
    """Exception raised when agent is not found."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(
            code="AGENT_NOT_FOUND",
            message=f"Agent not found: {agent_id}"
        )


class AgentService:
    """Service for agent management."""
    
    def __init__(self, db: Database):
        """Initialize AgentService.
        
        Args:
            db: Database instance for agent storage
        """
        self.db = db
    
    async def create(
        self,
        name: str,
        vault_id: str,
        system_prompt: str
    ) -> Agent:
        """Create a new agent.
        
        Args:
            name: Agent name
            vault_id: Associated vault ID
            system_prompt: System prompt for the agent
            
        Returns:
            Agent: Created agent object
        """
        logger.info("Creating agent", extra={"name": name, "vault_id": vault_id})
        
        # Generate unique agent_id
        agent_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        try:
            query = """
                INSERT INTO agents (agent_id, name, vault_id, system_prompt, created_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING agent_id, name, vault_id, system_prompt, created_at
            """
            
            row = await self.db.fetchrow(
                query,
                agent_id,
                name,
                vault_id,
                system_prompt,
                now
            )
            
            agent = Agent(
                agent_id=row["agent_id"],
                name=row["name"],
                vault_id=row["vault_id"],
                system_prompt=row["system_prompt"],
                created_at=row["created_at"]
            )
            
            logger.info(
                "Agent created successfully",
                extra={"agent_id": agent_id, "name": name}
            )
            
            return agent
            
        except Exception as e:
            logger.error(
                "Agent creation failed",
                extra={"name": name, "error": str(e)},
                exc_info=True
            )
            raise
    
    async def list_all(self, vault_id: Optional[str] = None) -> List[Agent]:
        """Retrieve all agents, optionally filtered by vault.
        
        Args:
            vault_id: Optional vault ID to filter agents
        
        Returns:
            List[Agent]: List of agents
        """
        logger.debug("Listing agents", extra={"vault_id": vault_id})
        
        if vault_id:
            query = """
                SELECT agent_id, name, vault_id, system_prompt, created_at
                FROM agents
                WHERE vault_id = $1
                ORDER BY created_at DESC
            """
            rows = await self.db.fetch(query, vault_id)
        else:
            query = """
                SELECT agent_id, name, vault_id, system_prompt, created_at
                FROM agents
                ORDER BY created_at DESC
            """
            rows = await self.db.fetch(query)
        
        agents = [
            Agent(
                agent_id=row["agent_id"],
                name=row["name"],
                vault_id=row["vault_id"],
                system_prompt=row["system_prompt"],
                created_at=row["created_at"]
            )
            for row in rows
        ]
        
        logger.info(f"Retrieved {len(agents)} agents")
        
        return agents
    
    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Retrieve agent by ID.
        
        Args:
            agent_id: Unique agent identifier
            
        Returns:
            Optional[Agent]: Agent object or None if not found
        """
        logger.debug("Retrieving agent by ID", extra={"agent_id": agent_id})
        
        query = """
            SELECT agent_id, name, vault_id, system_prompt, created_at
            FROM agents
            WHERE agent_id = $1
        """
        
        row = await self.db.fetchrow(query, agent_id)
        
        if row is None:
            logger.warning("Agent not found", extra={"agent_id": agent_id})
            return None
        
        agent = Agent(
            agent_id=row["agent_id"],
            name=row["name"],
            vault_id=row["vault_id"],
            system_prompt=row["system_prompt"],
            created_at=row["created_at"]
        )
        
        logger.info("Agent retrieved", extra={"agent_id": agent_id})
        
        return agent
    
    async def delete(self, agent_id: str) -> None:
        """Delete agent.
        
        Args:
            agent_id: Unique agent identifier
            
        Raises:
            AgentNotFoundError: If agent does not exist
        """
        logger.info("Deleting agent", extra={"agent_id": agent_id})
        
        # Check if agent exists
        agent = await self.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)
        
        try:
            query = "DELETE FROM agents WHERE agent_id = $1"
            await self.db.execute(query, agent_id)
            
            logger.info(
                "Agent deleted successfully",
                extra={"agent_id": agent_id}
            )
            
        except Exception as e:
            logger.error(
                "Agent deletion failed",
                extra={"agent_id": agent_id, "error": str(e)},
                exc_info=True
            )
            raise
