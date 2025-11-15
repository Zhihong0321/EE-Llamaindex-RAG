"""Configuration management for the RAG API Server.

This module provides configuration loading from environment variables
with validation and defaults as specified in Requirements 8.1-8.6.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Config(BaseSettings):
    """Application configuration loaded from environment variables.
    
    Required environment variables:
    - OPENAI_API_KEY: OpenAI API key for embeddings and chat
    - DB_URL: PostgreSQL connection string
    
    Optional environment variables (with defaults):
    - EMBEDDING_MODEL: OpenAI embedding model name
    - CHAT_MODEL: OpenAI chat model name
    - MAX_HISTORY_MESSAGES: Maximum number of messages to include in chat history
    - TOP_K_DEFAULT: Default number of documents to retrieve
    - HOST: Server host
    - PORT: Server port
    """
    
    # Required: OpenAI configuration (Requirement 8.1)
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key for embeddings and chat completion"
    )
    
    # Optional: OpenAI-compatible API base URL
    openai_api_base: str | None = Field(
        default=None,
        description="Custom base URL for OpenAI-compatible API (e.g., https://api.bltcy.ai)"
    )
    
    # Required: Database configuration (Requirement 8.2)
    db_url: str = Field(
        ...,
        description="PostgreSQL connection string with pgvector support"
    )
    
    # Optional: Model configuration with defaults (Requirements 8.3, 8.4)
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model name"
    )
    
    chat_model: str = Field(
        default="gpt-4.1-mini",
        description="OpenAI chat model name"
    )
    
    # Optional: Application behavior configuration (Requirements 8.5, 8.6)
    max_history_messages: int = Field(
        default=10,
        description="Maximum number of conversation messages to include in context"
    )
    
    top_k_default: int = Field(
        default=5,
        description="Default number of document chunks to retrieve for RAG"
    )
    
    # Optional: Server configuration
    default_temperature: float = Field(
        default=0.3,
        description="Default temperature for LLM responses"
    )
    
    host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    
    port: int = Field(
        default=8000,
        description="Server port"
    )
    
    version: str = Field(
        default="0.1.0",
        description="API version"
    )
    
    # Production configuration
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins (* for all)"
    )
    
    max_request_size: int = Field(
        default=10_485_760,  # 10MB
        description="Maximum request body size in bytes"
    )
    
    request_timeout: int = Field(
        default=60,
        description="Request timeout in seconds"
    )
    
    workers: int = Field(
        default=1,
        description="Number of Uvicorn worker processes"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v: str) -> str:
        """Validate that OpenAI API key is not empty."""
        if not v or not v.strip():
            raise ValueError("OPENAI_API_KEY must not be empty")
        return v.strip()
    
    @field_validator("db_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        """Validate that database URL is not empty and has basic format."""
        if not v or not v.strip():
            raise ValueError("DB_URL must not be empty")
        
        # Basic validation that it looks like a database URL
        v = v.strip()
        if not (v.startswith("postgresql://") or v.startswith("postgres://")):
            raise ValueError(
                "DB_URL must be a valid PostgreSQL connection string "
                "(starting with postgresql:// or postgres://)"
            )
        
        return v
    
    @field_validator("max_history_messages")
    @classmethod
    def validate_max_history_messages(cls, v: int) -> int:
        """Validate that max_history_messages is positive."""
        if v < 1:
            raise ValueError("MAX_HISTORY_MESSAGES must be at least 1")
        return v
    
    @field_validator("top_k_default")
    @classmethod
    def validate_top_k_default(cls, v: int) -> int:
        """Validate that top_k_default is positive."""
        if v < 1:
            raise ValueError("TOP_K_DEFAULT must be at least 1")
        return v
    
    @field_validator("default_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate that temperature is between 0 and 2."""
        if not 0 <= v <= 2:
            raise ValueError("default_temperature must be between 0 and 2")
        return v
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate that port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
        return v
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate that environment is a valid value."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of: {', '.join(valid_envs)}")
        return v.lower()
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_upper
    
    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string.
        
        Returns:
            List of allowed origins
        """
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    def is_production(self) -> bool:
        """Check if running in production environment.
        
        Returns:
            True if production, False otherwise
        """
        return self.environment == "production"


# Global config instance (to be initialized on app startup)
config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Config: The application configuration
        
    Raises:
        RuntimeError: If configuration has not been initialized
    """
    if config is None:
        raise RuntimeError(
            "Configuration not initialized. Call load_config() first."
        )
    return config


def load_config() -> Config:
    """Load configuration from environment variables.
    
    This should be called once during application startup.
    
    Returns:
        Config: The loaded configuration
        
    Raises:
        ValidationError: If required environment variables are missing or invalid
    """
    global config
    config = Config()
    return config
