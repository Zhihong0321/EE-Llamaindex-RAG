"""Pytest configuration and fixtures for integration tests."""

import asyncio
import os
import pytest
import asyncpg
from typing import AsyncGenerator
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Config
from app.db.database import Database


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Get test database URL from environment or use default.
    
    For integration tests, you can either:
    1. Set TEST_DB_URL environment variable to point to a test database
    2. Use the default DB_URL from .env (tests will create/drop tables)
    
    Note: Tests require a PostgreSQL database with pgvector extension.
    """
    # Try to get test-specific database URL
    test_url = os.getenv("TEST_DB_URL")
    if test_url:
        return test_url
    
    # Fall back to regular DB_URL (from .env)
    # This is acceptable for integration tests as we create/drop tables per test
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.getenv("DB_URL")
    if not db_url:
        pytest.skip("No database URL configured. Set TEST_DB_URL or DB_URL environment variable.")
    
    return db_url


@pytest.fixture(scope="session")
async def test_db_pool(test_db_url: str):
    """Create a database connection pool for tests."""
    pool = await asyncpg.create_pool(
        test_db_url,
        min_size=2,
        max_size=10
    )
    
    # Ensure pgvector extension is enabled
    async with pool.acquire() as conn:
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        except Exception:
            pass  # Extension might already exist
    
    yield pool
    
    await pool.close()


@pytest.fixture
async def test_db(test_db_pool) -> AsyncGenerator[Database, None]:
    """Create a Database instance and set up schema for each test."""
    db = Database(test_db_pool)
    
    # Create tables
    async with test_db_pool.acquire() as conn:
        # Sessions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Messages table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id BIGSERIAL PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Documents table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT,
                source TEXT,
                metadata_json JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # LlamaIndex vector store table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS data_llamaindex (
                id TEXT PRIMARY KEY,
                text TEXT,
                metadata_ JSONB,
                node_id TEXT,
                embedding vector(1536)
            )
        """)
    
    yield db
    
    # Clean up tables after each test
    async with test_db_pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS messages CASCADE")
        await conn.execute("DROP TABLE IF EXISTS sessions CASCADE")
        await conn.execute("DROP TABLE IF EXISTS documents CASCADE")
        await conn.execute("DROP TABLE IF EXISTS data_llamaindex CASCADE")


@pytest.fixture
def mock_config(test_db_url: str) -> Config:
    """Create a mock configuration for testing."""
    return Config(
        openai_api_key="test-api-key",
        openai_api_base="https://api.bltcy.ai",
        db_url=test_db_url,
        embedding_model="text-embedding-3-small",
        chat_model="gpt-5-nano-2025-08-07",
        max_history_messages=10,
        top_k_default=5,
        default_temperature=0.3,
        host="0.0.0.0",
        port=8000,
        version="0.1.0"
    )


@pytest.fixture
def mock_openai_embedding():
    """Mock OpenAI embedding model."""
    mock = MagicMock()
    mock.get_text_embedding = MagicMock(return_value=[0.1] * 1536)
    mock.get_text_embedding_batch = MagicMock(return_value=[[0.1] * 1536])
    return mock


@pytest.fixture
def mock_openai_llm():
    """Mock OpenAI LLM."""
    mock = MagicMock()
    
    # Mock chat response
    mock_response = MagicMock()
    mock_response.message.content = "This is a test response from the AI assistant."
    mock.chat = MagicMock(return_value=mock_response)
    
    return mock


@pytest.fixture
def mock_vector_store():
    """Mock pgvector store."""
    mock = MagicMock()
    mock.add = MagicMock()
    mock.query = MagicMock(return_value=MagicMock(nodes=[]))
    return mock


@pytest.fixture
def mock_index(mock_vector_store):
    """Mock VectorStoreIndex."""
    mock = MagicMock()
    mock.vector_store = mock_vector_store
    mock.insert = MagicMock()
    
    # Mock chat engine
    mock_chat_engine = MagicMock()
    mock_response = MagicMock()
    mock_response.response = "This is a test response from the AI assistant."
    mock_response.source_nodes = []
    mock_chat_engine.chat = MagicMock(return_value=mock_response)
    mock.as_chat_engine = MagicMock(return_value=mock_chat_engine)
    
    return mock


@pytest.fixture
def test_app(test_db, mock_config, mock_index, mock_openai_llm, mock_openai_embedding):
    """Create a test FastAPI app with mocked dependencies."""
    from fastapi import FastAPI
    from app.services.session_service import SessionService
    from app.services.message_service import MessageService
    from app.services.document_service import DocumentService
    from app.services.chat_service import ChatService
    from app.api import health, ingest, chat, documents
    
    # Create a test FastAPI app
    app = FastAPI(title="Test RAG API")
    
    # Initialize services with test database and mocked components
    session_service = SessionService(test_db)
    message_service = MessageService(test_db)
    document_service = DocumentService(test_db, mock_index)
    chat_service = ChatService(mock_index, mock_openai_llm, mock_config)
    
    # Wire services to API routers
    ingest.set_document_service(document_service)
    chat.set_services(session_service, message_service, chat_service, mock_config)
    documents.set_document_service(document_service)
    
    # Register routers
    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(chat.router)
    app.include_router(documents.router)
    
    return app


@pytest.fixture
async def test_client(test_app):
    """Create a test HTTP client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client
