"""LlamaIndex component initialization.

This module provides functions to initialize LlamaIndex components including:
- OpenAI embedding model (Requirement 6.1)
- OpenAI LLM for chat (Requirement 6.2)
- PGVector store for vector storage (Requirement 6.3)
- VectorStoreIndex for retrieval (Requirement 6.4)
- Global LlamaIndex Settings configuration (Requirement 6.5)
"""

from typing import Tuple
from urllib.parse import urlparse

from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.postgres import PGVectorStore

from app.config import Config
from app.llama.custom_openai import CustomOpenAI


def parse_db_url(db_url: str) -> dict:
    """Parse PostgreSQL connection URL into components.
    
    Args:
        db_url: PostgreSQL connection string (e.g., postgresql://user:pass@host:port/dbname)
        
    Returns:
        dict: Dictionary with keys: host, port, database, user, password
    """
    parsed = urlparse(db_url)
    
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") if parsed.path else "postgres",
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
    }


def initialize_embedding_model(config: Config) -> OpenAIEmbedding:
    """Initialize OpenAI embedding model.
    
    Requirement 6.1: Initialize the Embedding_Model using the model name 
    from EMBEDDING_MODEL environment variable.
    
    Args:
        config: Application configuration
        
    Returns:
        OpenAIEmbedding: Configured embedding model
    """
    kwargs = {
        "model": config.embedding_model,
        "api_key": config.openai_api_key,
    }
    
    # Add custom base URL if provided
    if config.openai_api_base:
        kwargs["api_base"] = config.openai_api_base
    
    embed_model = OpenAIEmbedding(**kwargs)
    
    return embed_model


def initialize_llm(config: Config) -> OpenAI:
    """Initialize OpenAI LLM for chat.
    
    Requirement 6.2: Initialize the Chat_Model using the model name 
    from CHAT_MODEL environment variable.
    
    Args:
        config: Application configuration
        
    Returns:
        OpenAI: Configured LLM (CustomOpenAI for custom endpoints)
    """
    kwargs = {
        "model": config.chat_model,
        "temperature": config.default_temperature,
        "api_key": config.openai_api_key,
    }
    
    # Use CustomOpenAI wrapper for custom API endpoints to bypass model validation
    if config.openai_api_base:
        kwargs["api_base"] = config.openai_api_base
        llm = CustomOpenAI(**kwargs)
    else:
        # Use standard OpenAI for official API
        llm = OpenAI(**kwargs)
    
    return llm


def initialize_vector_store(config: Config) -> PGVectorStore:
    """Initialize PGVector store for vector storage.
    
    Requirement 6.3: Connect to the Vector_Store using the connection string 
    from DB_URL environment variable.
    
    Args:
        config: Application configuration
        
    Returns:
        PGVectorStore: Configured vector store
    """
    # Parse database URL into components
    db_params = parse_db_url(config.db_url)
    
    # Initialize PGVectorStore with connection parameters
    vector_store = PGVectorStore.from_params(
        database=db_params["database"],
        host=db_params["host"],
        password=db_params["password"],
        port=db_params["port"],
        user=db_params["user"],
        table_name="embeddings",
        embed_dim=1536,  # Dimension for text-embedding-3-small
    )
    
    return vector_store


def initialize_index(vector_store: PGVectorStore, embed_model: OpenAIEmbedding) -> VectorStoreIndex:
    """Create VectorStoreIndex from vector store.
    
    Requirement 6.4: Create or load a vector index from the Vector_Store.
    
    Args:
        vector_store: Configured PGVector store
        embed_model: Configured embedding model
        
    Returns:
        VectorStoreIndex: Vector store index for retrieval
    """
    # Create storage context with vector store
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # Create index from vector store
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
        embed_model=embed_model,
    )
    
    return index


def configure_settings(embed_model: OpenAIEmbedding, llm: OpenAI) -> None:
    """Configure global LlamaIndex Settings.
    
    Requirement 6.5: Initialize the Chat_Engine from the vector index.
    This function configures the global Settings that will be used by
    chat engines and other LlamaIndex components.
    
    Args:
        embed_model: Configured embedding model
        llm: Configured LLM
    """
    Settings.llm = llm
    Settings.embed_model = embed_model


def initialize_llama_components(config: Config) -> Tuple[VectorStoreIndex, OpenAI, OpenAIEmbedding]:
    """Initialize all LlamaIndex components.
    
    This is a convenience function that initializes all components in the correct order:
    1. Embedding model (Requirement 6.1)
    2. LLM (Requirement 6.2)
    3. Vector store (Requirement 6.3)
    4. Vector index (Requirement 6.4)
    5. Global settings (Requirement 6.5)
    
    Args:
        config: Application configuration
        
    Returns:
        Tuple containing:
        - VectorStoreIndex: Vector store index for retrieval
        - OpenAI: Configured LLM
        - OpenAIEmbedding: Configured embedding model
    """
    # Initialize embedding model
    embed_model = initialize_embedding_model(config)
    
    # Initialize LLM
    llm = initialize_llm(config)
    
    # Initialize vector store
    vector_store = initialize_vector_store(config)
    
    # Create index from vector store
    index = initialize_index(vector_store, embed_model)
    
    # Configure global settings
    configure_settings(embed_model, llm)
    
    return index, llm, embed_model
