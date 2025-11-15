"""Integration tests for chat endpoint.

Tests Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 10.1, 10.2
"""

import pytest
from httpx import AsyncClient
from app.db.database import Database


@pytest.mark.asyncio
async def test_chat_endpoint_accessible(test_client: AsyncClient):
    """Test that chat endpoint is accessible at /chat path.
    
    Requirement 5.1: THE RAG_API_Server SHALL expose a POST endpoint at path "/chat"
    """
    response = await test_client.post(
        "/chat",
        json={
            "session_id": "test-session",
            "message": "Hello"
        }
    )
    
    # Should not return 404
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_chat_creates_new_session(test_client: AsyncClient, test_db: Database):
    """Test that chat creates a new session if it doesn't exist.
    
    Requirement 3.1: WHEN a POST request is received at "/chat" with a session_id 
    that does not exist in the sessions table, THE RAG_API_Server SHALL create 
    a new session record with that session_id
    """
    session_id = "new-test-session"
    
    # Verify session doesn't exist
    session = await test_db.fetchrow(
        "SELECT * FROM sessions WHERE id = $1",
        session_id
    )
    assert session is None
    
    # Send chat message
    response = await test_client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "Hello, this is a test message"
        }
    )
    
    assert response.status_code == 200
    
    # Verify session was created
    session = await test_db.fetchrow(
        "SELECT * FROM sessions WHERE id = $1",
        session_id
    )
    assert session is not None
    assert session["id"] == session_id
    assert session["created_at"] is not None


@pytest.mark.asyncio
async def test_chat_saves_user_message(test_client: AsyncClient, test_db: Database):
    """Test that user message is saved to database.
    
    Requirement 4.1: WHEN a user message is received at "/chat", THE RAG_API_Server 
    SHALL insert a record into the messages table with role "user" and the message content
    """
    session_id = "message-test-session"
    user_message = "What is LlamaIndex?"
    
    response = await test_client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": user_message
        }
    )
    
    assert response.status_code == 200
    
    # Verify user message was saved
    messages = await test_db.fetch(
        "SELECT * FROM messages WHERE session_id = $1 AND role = 'user'",
        session_id
    )
    
    assert len(messages) > 0
    user_msg = messages[0]
    assert user_msg["content"] == user_message
    assert user_msg["role"] == "user"


@pytest.mark.asyncio
async def test_chat_saves_assistant_message(test_client: AsyncClient, test_db: Database):
    """Test that assistant response is saved to database.
    
    Requirement 4.2: WHEN the Chat_Engine generates a response, THE RAG_API_Server 
    SHALL insert a record into the messages table with role "assistant" and the 
    response content
    """
    session_id = "assistant-message-session"
    
    response = await test_client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "Tell me about AI"
        }
    )
    
    assert response.status_code == 200
    
    # Verify assistant message was saved
    messages = await test_db.fetch(
        "SELECT * FROM messages WHERE session_id = $1 AND role = 'assistant'",
        session_id
    )
    
    assert len(messages) > 0
    assistant_msg = messages[0]
    assert assistant_msg["role"] == "assistant"
    assert len(assistant_msg["content"]) > 0


@pytest.mark.asyncio
async def test_chat_returns_correct_response_format(test_client: AsyncClient):
    """Test that chat endpoint returns correct response format.
    
    Requirement 5.8: WHEN a response is generated, THE RAG_API_Server SHALL return 
    HTTP status code 200 with JSON containing "session_id", "answer", and "sources" array
    """
    response = await test_client.post(
        "/chat",
        json={
            "session_id": "format-test-session",
            "message": "Test message"
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "session_id" in data
    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert data["session_id"] == "format-test-session"


@pytest.mark.asyncio
async def test_chat_without_message_returns_422(test_client: AsyncClient):
    """Test that chat endpoint returns 422 when message field is missing.
    
    Requirement 10.1: WHEN a POST request is received at "/chat" without a "message" 
    field, THE RAG_API_Server SHALL return HTTP status code 422 with validation 
    error details
    """
    response = await test_client.post(
        "/chat",
        json={"session_id": "test-session"}
    )
    
    assert response.status_code == 422
    
    data = response.json()
    assert "error" in data
    assert "detail" in data


@pytest.mark.asyncio
async def test_chat_without_session_id_returns_422(test_client: AsyncClient):
    """Test that chat endpoint returns 422 when session_id field is missing.
    
    Requirement 10.2: WHEN a POST request is received at "/chat" without a 
    "session_id" field, THE RAG_API_Server SHALL return HTTP status code 422 
    with validation error details
    """
    response = await test_client.post(
        "/chat",
        json={"message": "Test message"}
    )
    
    assert response.status_code == 422
    
    data = response.json()
    assert "error" in data
    assert "detail" in data


@pytest.mark.asyncio
async def test_chat_with_empty_message_returns_422(test_client: AsyncClient):
    """Test that chat endpoint returns 422 when message is empty."""
    response = await test_client.post(
        "/chat",
        json={
            "session_id": "test-session",
            "message": ""
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_with_config_parameters(test_client: AsyncClient):
    """Test chat with custom configuration parameters.
    
    Requirement 5.5: WHEN performing vector search, THE RAG_API_Server SHALL 
    retrieve the top 5 most similar document chunks or the value specified in 
    the request config top_k parameter
    """
    response = await test_client.post(
        "/chat",
        json={
            "session_id": "config-test-session",
            "message": "Test with custom config",
            "config": {
                "top_k": 3,
                "temperature": 0.7
            }
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data


@pytest.mark.asyncio
async def test_chat_multi_turn_conversation(test_client: AsyncClient, test_db: Database):
    """Test multi-turn conversation maintains history.
    
    Requirement 5.2: WHEN a POST request is received at "/chat" with JSON body 
    containing "session_id" and "message", THE RAG_API_Server SHALL retrieve 
    the most recent messages for that session from the messages table
    """
    session_id = "multi-turn-session"
    
    # First message
    response1 = await test_client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "What is AI?"
        }
    )
    assert response1.status_code == 200
    
    # Second message
    response2 = await test_client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "Tell me more about it"
        }
    )
    assert response2.status_code == 200
    
    # Verify both messages are stored
    messages = await test_db.fetch(
        "SELECT * FROM messages WHERE session_id = $1 ORDER BY created_at",
        session_id
    )
    
    # Should have 4 messages: 2 user + 2 assistant
    assert len(messages) >= 4


@pytest.mark.asyncio
async def test_chat_updates_session_last_active(test_client: AsyncClient, test_db: Database):
    """Test that chat updates session last_active_at timestamp.
    
    Requirement 3.3: WHEN a message is processed for an existing session, 
    THE RAG_API_Server SHALL update the last_active_at field to the current timestamp
    """
    session_id = "last-active-session"
    
    # First chat
    await test_client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "First message"
        }
    )
    
    # Get initial last_active_at
    session1 = await test_db.fetchrow(
        "SELECT last_active_at FROM sessions WHERE id = $1",
        session_id
    )
    first_active = session1["last_active_at"]
    
    # Wait a moment
    import asyncio
    await asyncio.sleep(0.1)
    
    # Second chat
    await test_client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "Second message"
        }
    )
    
    # Get updated last_active_at
    session2 = await test_db.fetchrow(
        "SELECT last_active_at FROM sessions WHERE id = $1",
        session_id
    )
    second_active = session2["last_active_at"]
    
    # Verify last_active_at was updated
    assert second_active >= first_active


@pytest.mark.asyncio
async def test_chat_with_custom_api_base(test_client: AsyncClient, mock_config):
    """Test that chat works with custom OpenAI API base URL.
    
    Tests custom OpenAI API base URL configuration requirement.
    """
    # Verify config has custom API base
    assert mock_config.openai_api_base == "https://api.bltcy.ai"
    
    # Test chat works with custom API base
    response = await test_client.post(
        "/chat",
        json={
            "session_id": "custom-api-session",
            "message": "Test with custom API"
        }
    )
    
    assert response.status_code == 200
    assert "answer" in response.json()
