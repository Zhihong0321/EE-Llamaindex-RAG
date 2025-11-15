"""Database connection and query utilities using asyncpg."""

import asyncpg
from typing import Any, List, Optional


class Database:
    """Database wrapper for asyncpg connection pool."""
    
    def __init__(self, pool: asyncpg.Pool):
        """Initialize database with connection pool.
        
        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query that doesn't return results.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Status string from query execution
        """
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows from a query.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            List of database records
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row from a query.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Single database record or None
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value from a query.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Single value from query result
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


async def create_pool(db_url: str, min_size: int = 5, max_size: int = 20) -> asyncpg.Pool:
    """Create asyncpg connection pool.
    
    Args:
        db_url: Database connection URL
        min_size: Minimum number of connections in pool
        max_size: Maximum number of connections in pool
        
    Returns:
        asyncpg connection pool
    """
    return await asyncpg.create_pool(
        dsn=db_url,
        min_size=min_size,
        max_size=max_size
    )
