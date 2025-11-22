"""FastAPI application initialization and component wiring.

This module creates the FastAPI application and wires together all components:
- Database connection pool
- LlamaIndex components (embeddings, LLM, vector store, index)
- Service layer (SessionService, MessageService, DocumentService, ChatService)
- API routers (health, ingest, chat, documents)
- Exception handlers
- Logging and middleware

Requirements: 1.1, 2.1, 5.1, 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 10.1, 10.2, 10.3, 10.4
"""

import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError

from app.config import load_config
from app.db.database import create_pool, Database
from app.llama.setup import initialize_llama_components
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.services.document_service import DocumentService
from app.services.chat_service import ChatService
from app.services.vault_service import VaultService, VaultNotFoundError, VaultAlreadyExistsError
from app.logging_config import setup_logging, get_logger
from app.middleware import RequestLoggingMiddleware
from app.exceptions import (
    RAGAPIException,
    SessionNotFoundError,
    DocumentIngestError,
    DocumentNotFoundError,
    ChatGenerationError,
    MessageSaveError,
    DatabaseConnectionError,
    OpenAIServiceError,
)

# Import API routers
from app.api import health, ingest, chat, documents, vaults


# Logger will be initialized after config is loaded
logger = None


# Global state for cleanup
app_state = {
    "db_pool": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events.
    
    Startup:
    - Load configuration
    - Initialize database connection pool
    - Initialize LlamaIndex components
    - Initialize services
    - Wire services to API routers
    
    Shutdown:
    - Close database connection pool
    """
    # Startup: Initialize all components
    try:
        # Load configuration from environment variables
        config = load_config()
        
        # Set up logging with configured level
        global logger
        setup_logging(log_level=config.log_level)
        logger = get_logger(__name__)
        
        logger.info(
            "Starting up RAG API Server...",
            extra={
                "version": config.version,
                "environment": config.environment,
                "log_level": config.log_level
            }
        )
        
        # Log CORS configuration
        cors_origins = config.get_cors_origins_list()
        logger.info(
            "CORS configured",
            extra={
                "origins": cors_origins if cors_origins != ["*"] else "all origins (development only)"
            }
        )
        
        # Run database migrations
        logger.info("Running database migrations...")
        try:
            from alembic.config import Config as AlembicConfig
            from alembic import command
            alembic_cfg = AlembicConfig("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", config.db_url)
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed")
        except Exception as e:
            logger.warning(f"Migration warning (may be already applied): {e}")
        
        # Initialize database connection pool
        logger.info("Connecting to database...")
        try:
            db_pool = await create_pool(config.db_url, min_size=5, max_size=20)
            app_state["db_pool"] = db_pool
            db = Database(db_pool)
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to connect to database", exc_info=True)
            raise DatabaseConnectionError(str(e))
        
        # Initialize LlamaIndex components (Requirements 6.1, 6.2, 6.3, 6.4, 6.5)
        logger.info("Initializing LlamaIndex components...")
        try:
            index, llm, embed_model = initialize_llama_components(config)
            logger.info(
                "LlamaIndex initialized",
                extra={
                    "embedding_model": config.embedding_model,
                    "chat_model": config.chat_model
                }
            )
        except Exception as e:
            logger.error("Failed to initialize LlamaIndex components", exc_info=True)
            raise OpenAIServiceError("initialization", str(e))
        
        # Initialize services
        logger.info("Initializing services...")
        session_service = SessionService(db)
        message_service = MessageService(db)
        document_service = DocumentService(db, index)
        chat_service = ChatService(index, llm, config)
        vault_service = VaultService(db)
        logger.info("Services initialized")
        
        # Wire services to API routers
        logger.info("Wiring services to API routers...")
        ingest.set_document_service(document_service)
        chat.set_services(session_service, message_service, chat_service, config)
        documents.set_document_service(document_service)
        vaults.set_vault_service(vault_service)
        logger.info("Services wired to API routers")
        
        logger.info(
            "RAG API Server startup complete",
            extra={
                "environment": config.environment,
                "version": config.version
            }
        )
        
    except Exception as e:
        logger.error("Failed to start RAG API Server", exc_info=True)
        raise
    
    yield
    
    # Shutdown: Clean up resources
    logger.info("Shutting down RAG API Server...")
    
    try:
        # Close database connection pool
        if app_state["db_pool"]:
            await app_state["db_pool"].close()
            logger.info("Database connection pool closed")
    except Exception as e:
        logger.error("Error during shutdown", exc_info=True)
    
    logger.info("RAG API Server shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="LlamaIndex RAG API",
    description="Conversational RAG API with LlamaIndex, FastAPI, and PostgreSQL",
    version="0.1.0",
    lifespan=lifespan,
)


# Add response middleware to ensure CORS headers on all responses
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Configure middleware (must be done before app starts)
# Add request logging middleware (Requirement 10.4)
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS - Allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# Register API routers
# Requirement 1.1: Health check endpoint
app.include_router(health.router, tags=["health"])

# Requirement 2.1: Document ingestion endpoint
app.include_router(ingest.router, tags=["ingest"])

# Requirement 5.1: Chat endpoint
app.include_router(chat.router, tags=["chat"])

# Requirement 9.1: Documents listing endpoint (optional feature)
app.include_router(documents.router, tags=["documents"])

# Vault management endpoints
app.include_router(vaults.router, tags=["vaults"])


# Exception Handlers (Requirements 10.1, 10.2, 10.3, 10.4)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI request validation errors (Requirements 10.1, 10.2, 10.3).
    
    Returns 422 status code with detailed validation error information.
    """
    logger.warning(
        "Request validation error",
        extra={
            "path": request.url.path,
            "errors": exc.errors(),
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "code": "VALIDATION_ERROR"
        }
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
    """Handle Pydantic validation errors from models (Requirements 10.1, 10.2, 10.3).
    
    Returns 422 status code with detailed validation error information.
    """
    logger.warning(
        "Pydantic validation error",
        extra={
            "path": request.url.path,
            "errors": exc.errors(),
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "code": "VALIDATION_ERROR"
        }
    )


@app.exception_handler(SessionNotFoundError)
async def session_not_found_handler(request: Request, exc: SessionNotFoundError):
    """Handle session not found errors (Requirement 10.4).
    
    Returns 404 status code.
    """
    logger.warning(
        "Session not found",
        extra={
            "session_id": exc.session_id,
            "path": request.url.path,
        }
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": exc.message,
            "detail": f"Session {exc.session_id} does not exist",
            "code": exc.code
        }
    )


@app.exception_handler(DocumentNotFoundError)
async def document_not_found_handler(request: Request, exc: DocumentNotFoundError):
    """Handle document not found errors (Requirement 10.4).
    
    Returns 404 status code.
    """
    logger.warning(
        "Document not found",
        extra={
            "document_id": exc.document_id,
            "path": request.url.path,
        }
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": exc.message,
            "detail": f"Document {exc.document_id} does not exist",
            "code": exc.code
        }
    )


@app.exception_handler(VaultNotFoundError)
async def vault_not_found_handler(request: Request, exc: VaultNotFoundError):
    """Handle vault not found errors.
    
    Returns 404 status code.
    """
    logger.warning(
        "Vault not found",
        extra={
            "vault_id": exc.vault_id,
            "path": request.url.path,
        }
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": exc.message,
            "detail": f"Vault {exc.vault_id} does not exist",
            "code": exc.code
        }
    )


@app.exception_handler(VaultAlreadyExistsError)
async def vault_already_exists_handler(request: Request, exc: VaultAlreadyExistsError):
    """Handle vault already exists errors.
    
    Returns 409 status code.
    """
    logger.warning(
        "Vault already exists",
        extra={
            "name": exc.name,
            "path": request.url.path,
        }
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": exc.message,
            "detail": f"Vault with name '{exc.name}' already exists",
            "code": exc.code
        }
    )


@app.exception_handler(DocumentIngestError)
async def document_ingest_error_handler(request: Request, exc: DocumentIngestError):
    """Handle document ingestion errors (Requirement 10.3, 10.4).
    
    Returns 500 status code.
    """
    logger.error(
        "Document ingestion failed",
        extra={
            "document_id": exc.document_id,
            "reason": exc.reason,
            "path": request.url.path,
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": exc.message,
            "detail": exc.reason,
            "code": exc.code
        }
    )


@app.exception_handler(ChatGenerationError)
async def chat_generation_error_handler(request: Request, exc: ChatGenerationError):
    """Handle chat generation errors (Requirement 10.1, 10.2, 10.4).
    
    Returns 500 status code.
    """
    logger.error(
        "Chat generation failed",
        extra={
            "session_id": exc.session_id,
            "reason": exc.reason,
            "path": request.url.path,
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": exc.message,
            "detail": exc.reason,
            "code": exc.code
        }
    )


@app.exception_handler(MessageSaveError)
async def message_save_error_handler(request: Request, exc: MessageSaveError):
    """Handle message save errors (Requirement 10.1, 10.2, 10.4).
    
    Returns 500 status code.
    """
    logger.error(
        "Message save failed",
        extra={
            "session_id": exc.session_id,
            "reason": exc.reason,
            "path": request.url.path,
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": exc.message,
            "detail": exc.reason,
            "code": exc.code
        }
    )


@app.exception_handler(DatabaseConnectionError)
async def database_connection_error_handler(request: Request, exc: DatabaseConnectionError):
    """Handle database connection errors (Requirement 10.4).
    
    Returns 503 status code.
    """
    logger.error(
        "Database connection error",
        extra={
            "reason": exc.reason,
            "path": request.url.path,
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": exc.message,
            "detail": "Database service is unavailable",
            "code": exc.code
        }
    )


@app.exception_handler(OpenAIServiceError)
async def openai_service_error_handler(request: Request, exc: OpenAIServiceError):
    """Handle OpenAI service errors (Requirement 10.4).
    
    Returns 502 status code.
    """
    logger.error(
        "OpenAI service error",
        extra={
            "operation": exc.operation,
            "reason": exc.reason,
            "path": request.url.path,
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": exc.message,
            "detail": "Failed to communicate with OpenAI API",
            "code": exc.code
        }
    )


@app.exception_handler(RAGAPIException)
async def rag_api_exception_handler(request: Request, exc: RAGAPIException):
    """Handle custom RAG API exceptions (Requirement 10.4).
    
    Returns 500 status code for generic RAG API errors.
    """
    logger.error(
        "RAG API error",
        extra={
            "error_code": exc.code,
            "message": exc.message,
            "path": request.url.path,
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": exc.message,
            "detail": str(exc),
            "code": exc.code
        }
    )


@app.exception_handler(asyncpg.PostgresError)
async def database_exception_handler(request: Request, exc: asyncpg.PostgresError):
    """Handle PostgreSQL database errors (Requirement 10.4).
    
    Returns 500 status code for database errors.
    """
    logger.error(
        "Database error",
        extra={
            "path": request.url.path,
            "error": str(exc),
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error",
            "detail": "An error occurred while accessing the database",
            "code": "DATABASE_ERROR"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other unhandled exceptions (Requirement 10.4).
    
    Returns appropriate status code based on exception type.
    """
    # Check if it's an OpenAI error
    exc_type = type(exc).__name__
    exc_module = str(type(exc).__module__)
    
    if "openai" in exc_type.lower() or "openai" in exc_module.lower():
        logger.error(
            "OpenAI API error",
            extra={
                "path": request.url.path,
                "error_type": exc_type,
            },
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error": "External service error",
                "detail": "Failed to communicate with OpenAI API",
                "code": "OPENAI_ERROR"
            }
        )
    
    # Generic internal server error
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "error_type": exc_type,
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "code": "INTERNAL_ERROR"
        }
    )


# Root endpoint for basic info
@app.get("/", tags=["root"])
async def root():
    """Root endpoint providing basic API information."""
    return {
        "name": "LlamaIndex RAG API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ingest": "/ingest",
            "chat": "/chat",
            "documents": "/documents",
            "vaults": "/vaults",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Load config to get port
    config = load_config()
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=True,  # Enable auto-reload for development
    )
