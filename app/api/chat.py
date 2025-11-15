"""Chat endpoint for conversational RAG interactions.

This module implements the POST /chat endpoint for conversational interactions
with the RAG system (Requirements 5.1-5.9, 10.1, 10.2).
"""

from fastapi import APIRouter, HTTPException, status

from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.services.chat_service import ChatService
from app.config import Config


router = APIRouter()

# These will be injected via dependency injection in main.py
session_service: SessionService = None
message_service: MessageService = None
chat_service: ChatService = None
config: Config = None


def set_services(
    session_svc: SessionService,
    message_svc: MessageService,
    chat_svc: ChatService,
    cfg: Config
) -> None:
    """Set the service instances.
    
    Args:
        session_svc: SessionService instance for session management
        message_svc: MessageService instance for message handling
        chat_svc: ChatService instance for chat generation
        cfg: Application configuration
    """
    global session_service, message_service, chat_service, config
    session_service = session_svc
    message_service = message_svc
    chat_service = chat_svc
    config = cfg


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle chat requests with RAG-based response generation.
    
    This endpoint implements the full conversational RAG flow:
    1. Get or create session
    2. Update session activity timestamp
    3. Save user message
    4. Retrieve recent conversation history
    5. Generate RAG response with context
    6. Save assistant response
    7. Return response with sources
    
    Requirements:
    - 5.1: Expose POST endpoint at "/chat"
    - 5.2: Retrieve most recent messages for session
    - 5.3: Limit history to MAX_HISTORY_MESSAGES
    - 5.4: Perform vector similarity search
    - 5.5: Retrieve top K document chunks
    - 5.6: Provide context and history to Chat_Engine
    - 5.7: Generate response using Chat_Model
    - 5.8: Return session_id, answer, and sources
    - 5.9: Include document_id, title, snippet, and score for each source
    - 10.1: Validate required "message" field (handled by Pydantic)
    - 10.2: Validate required "session_id" field (handled by Pydantic)
    
    Args:
        request: ChatRequest containing session_id, message, and optional config
        
    Returns:
        ChatResponse: Contains session_id, answer, and sources
        
    Raises:
        HTTPException: 422 if validation fails (handled by FastAPI)
        HTTPException: 500 if chat generation fails
    """
    # Verify services are initialized
    if not all([session_service, message_service, chat_service, config]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Services not initialized"
        )
    
    try:
        # Step 1: Get or create session (Requirement 3.1, 3.2)
        session = await session_service.get_or_create_session(
            session_id=request.session_id
        )
        
        # Step 2: Update last_active timestamp (Requirement 3.3)
        await session_service.update_last_active(request.session_id)
        
        # Step 3: Save user message (Requirement 4.1)
        await message_service.save_message(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
        
        # Step 4: Retrieve recent messages (Requirements 5.2, 5.3)
        # Use MAX_HISTORY_MESSAGES from config
        recent_messages = await message_service.get_recent_messages(
            session_id=request.session_id,
            limit=config.max_history_messages
        )
        
        # Convert to LlamaIndex ChatMessage format
        chat_history = message_service.format_for_chat_engine(recent_messages)
        
        # Step 5: Generate RAG response (Requirements 5.4, 5.5, 5.6, 5.7, 5.9)
        answer, sources = await chat_service.generate_response(
            message=request.message,
            chat_history=chat_history,
            top_k=request.config.top_k,
            temperature=request.config.temperature,
            session_id=request.session_id
        )
        
        # Step 6: Save assistant message (Requirement 4.2)
        await message_service.save_message(
            session_id=request.session_id,
            role="assistant",
            content=answer
        )
        
        # Step 7: Return response (Requirement 5.8)
        return ChatResponse(
            session_id=request.session_id,
            answer=answer,
            sources=sources
        )
        
    except ValueError as e:
        # Handle validation errors from services
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Error handling for chat failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate chat response: {str(e)}"
        )
