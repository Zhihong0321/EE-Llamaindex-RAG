"""Unit tests for MessageService."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from llama_index.core.llms import ChatMessage, MessageRole as LlamaMessageRole

from app.services.message_service import MessageService
from app.models.database import Message, MessageRole
from app.exceptions import MessageSaveError


@pytest.fixture
def mock_db():
    """Create a mock database instance."""
    db = MagicMock()
    db.fetchrow = AsyncMock()
    db.fetch = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def message_service(mock_db):
    """Create MessageService instance with mock database."""
    return MessageService(db=mock_db)


@pytest.mark.asyncio
async def test_save_message_user_role(message_service, mock_db):
    """Test saving a user message."""
    # Arrange
    session_id = "session_123"
    role = "user"
    content = "Hello, how are you?"
    created_at = datetime(2024, 1, 1, 12, 0, 0)
    
    mock_db.fetchrow.return_value = {
        'id': 1,
        'session_id': session_id,
        'role': role,
        'content': content,
        'created_at': created_at
    }
    
    # Act
    result = await message_service.save_message(session_id, role, content)
    
    # Assert
    assert isinstance(result, Message)
    assert result.id == 1
    assert result.session_id == session_id
    assert result.role == MessageRole.USER
    assert result.content == content
    assert result.created_at == created_at
    
    mock_db.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_save_message_assistant_role(message_service, mock_db):
    """Test saving an assistant message."""
    # Arrange
    session_id = "session_456"
    role = "assistant"
    content = "I'm doing well, thank you!"
    created_at = datetime(2024, 1, 1, 12, 1, 0)
    
    mock_db.fetchrow.return_value = {
        'id': 2,
        'session_id': session_id,
        'role': role,
        'content': content,
        'created_at': created_at
    }
    
    # Act
    result = await message_service.save_message(session_id, role, content)
    
    # Assert
    assert result.role == MessageRole.ASSISTANT


@pytest.mark.asyncio
async def test_save_message_system_role(message_service, mock_db):
    """Test saving a system message."""
    # Arrange
    session_id = "session_789"
    role = "system"
    content = "You are a helpful assistant."
    created_at = datetime(2024, 1, 1, 12, 2, 0)
    
    mock_db.fetchrow.return_value = {
        'id': 3,
        'session_id': session_id,
        'role': role,
        'content': content,
        'created_at': created_at
    }
    
    # Act
    result = await message_service.save_message(session_id, role, content)
    
    # Assert
    assert result.role == MessageRole.SYSTEM


@pytest.mark.asyncio
async def test_save_message_invalid_role(message_service, mock_db):
    """Test saving a message with invalid role raises ValueError."""
    # Arrange
    session_id = "session_invalid"
    role = "invalid_role"
    content = "This should fail"
    
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        await message_service.save_message(session_id, role, content)
    
    assert "Invalid role" in str(exc_info.value)
    mock_db.fetchrow.assert_not_called()


@pytest.mark.asyncio
async def test_save_message_database_error(message_service, mock_db):
    """Test saving a message when database fails."""
    # Arrange
    session_id = "session_error"
    role = "user"
    content = "Test message"
    
    mock_db.fetchrow.side_effect = Exception("Database connection failed")
    
    # Act & Assert
    with pytest.raises(MessageSaveError) as exc_info:
        await message_service.save_message(session_id, role, content)
    
    assert session_id in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_recent_messages(message_service, mock_db):
    """Test retrieving recent messages for a session."""
    # Arrange
    session_id = "session_history"
    created_at_1 = datetime(2024, 1, 1, 12, 0, 0)
    created_at_2 = datetime(2024, 1, 1, 12, 1, 0)
    created_at_3 = datetime(2024, 1, 1, 12, 2, 0)
    
    # Messages returned in DESC order (newest first)
    mock_db.fetch.return_value = [
        {
            'id': 3,
            'session_id': session_id,
            'role': 'assistant',
            'content': 'Response 2',
            'created_at': created_at_3
        },
        {
            'id': 2,
            'session_id': session_id,
            'role': 'user',
            'content': 'Question 2',
            'created_at': created_at_2
        },
        {
            'id': 1,
            'session_id': session_id,
            'role': 'user',
            'content': 'Question 1',
            'created_at': created_at_1
        }
    ]
    
    # Act
    result = await message_service.get_recent_messages(session_id, limit=10)
    
    # Assert
    assert len(result) == 3
    # Messages should be in chronological order (oldest first)
    assert result[0].id == 1
    assert result[0].content == 'Question 1'
    assert result[1].id == 2
    assert result[1].content == 'Question 2'
    assert result[2].id == 3
    assert result[2].content == 'Response 2'
    
    mock_db.fetch.assert_called_once()


@pytest.mark.asyncio
async def test_get_recent_messages_with_limit(message_service, mock_db):
    """Test retrieving messages with custom limit."""
    # Arrange
    session_id = "session_limit"
    mock_db.fetch.return_value = []
    
    # Act
    await message_service.get_recent_messages(session_id, limit=5)
    
    # Assert
    call_args = mock_db.fetch.call_args
    # Verify limit is passed to query
    assert 5 in call_args[0]


@pytest.mark.asyncio
async def test_get_recent_messages_empty(message_service, mock_db):
    """Test retrieving messages when none exist."""
    # Arrange
    session_id = "session_empty"
    mock_db.fetch.return_value = []
    
    # Act
    result = await message_service.get_recent_messages(session_id)
    
    # Assert
    assert result == []


def test_format_for_chat_engine_user_message(message_service):
    """Test formatting user message for chat engine."""
    # Arrange
    messages = [
        Message(
            id=1,
            session_id="session_1",
            role=MessageRole.USER,
            content="Hello",
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
    ]
    
    # Act
    result = message_service.format_for_chat_engine(messages)
    
    # Assert
    assert len(result) == 1
    assert isinstance(result[0], ChatMessage)
    assert result[0].role == LlamaMessageRole.USER
    assert result[0].content == "Hello"


def test_format_for_chat_engine_assistant_message(message_service):
    """Test formatting assistant message for chat engine."""
    # Arrange
    messages = [
        Message(
            id=2,
            session_id="session_1",
            role=MessageRole.ASSISTANT,
            content="Hi there!",
            created_at=datetime(2024, 1, 1, 12, 1, 0)
        )
    ]
    
    # Act
    result = message_service.format_for_chat_engine(messages)
    
    # Assert
    assert result[0].role == LlamaMessageRole.ASSISTANT
    assert result[0].content == "Hi there!"


def test_format_for_chat_engine_system_message(message_service):
    """Test formatting system message for chat engine."""
    # Arrange
    messages = [
        Message(
            id=3,
            session_id="session_1",
            role=MessageRole.SYSTEM,
            content="You are helpful",
            created_at=datetime(2024, 1, 1, 12, 2, 0)
        )
    ]
    
    # Act
    result = message_service.format_for_chat_engine(messages)
    
    # Assert
    assert result[0].role == LlamaMessageRole.SYSTEM


def test_format_for_chat_engine_multiple_messages(message_service):
    """Test formatting multiple messages for chat engine."""
    # Arrange
    messages = [
        Message(
            id=1,
            session_id="session_1",
            role=MessageRole.USER,
            content="Question 1",
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        ),
        Message(
            id=2,
            session_id="session_1",
            role=MessageRole.ASSISTANT,
            content="Answer 1",
            created_at=datetime(2024, 1, 1, 12, 1, 0)
        ),
        Message(
            id=3,
            session_id="session_1",
            role=MessageRole.USER,
            content="Question 2",
            created_at=datetime(2024, 1, 1, 12, 2, 0)
        )
    ]
    
    # Act
    result = message_service.format_for_chat_engine(messages)
    
    # Assert
    assert len(result) == 3
    assert result[0].role == LlamaMessageRole.USER
    assert result[1].role == LlamaMessageRole.ASSISTANT
    assert result[2].role == LlamaMessageRole.USER


def test_format_for_chat_engine_empty_list(message_service):
    """Test formatting empty message list."""
    # Arrange
    messages = []
    
    # Act
    result = message_service.format_for_chat_engine(messages)
    
    # Assert
    assert result == []
