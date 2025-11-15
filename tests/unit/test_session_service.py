"""Unit tests for SessionService."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.services.session_service import SessionService
from app.models.database import Session


@pytest.fixture
def mock_db():
    """Create a mock database instance."""
    db = MagicMock()
    db.fetchrow = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def session_service(mock_db):
    """Create SessionService instance with mock database."""
    return SessionService(db=mock_db)


@pytest.mark.asyncio
async def test_get_or_create_session_existing(session_service, mock_db):
    """Test getting an existing session."""
    # Arrange
    session_id = "test_session_123"
    user_id = "user_456"
    created_at = datetime(2024, 1, 1, 12, 0, 0)
    last_active_at = datetime(2024, 1, 1, 13, 0, 0)
    
    mock_db.fetchrow.return_value = {
        'id': session_id,
        'user_id': user_id,
        'created_at': created_at,
        'last_active_at': last_active_at
    }
    
    # Act
    result = await session_service.get_or_create_session(session_id, user_id)
    
    # Assert
    assert isinstance(result, Session)
    assert result.id == session_id
    assert result.user_id == user_id
    assert result.created_at == created_at
    assert result.last_active_at == last_active_at
    
    # Verify database was queried
    mock_db.fetchrow.assert_called_once()
    call_args = mock_db.fetchrow.call_args
    assert session_id in call_args[0]


@pytest.mark.asyncio
async def test_get_or_create_session_new(session_service, mock_db):
    """Test creating a new session when it doesn't exist."""
    # Arrange
    session_id = "new_session_789"
    user_id = "user_123"
    created_at = datetime(2024, 1, 2, 10, 0, 0)
    
    # First call returns None (session doesn't exist)
    # Second call returns the newly created session
    mock_db.fetchrow.side_effect = [
        None,
        {
            'id': session_id,
            'user_id': user_id,
            'created_at': created_at,
            'last_active_at': created_at
        }
    ]
    
    # Act
    result = await session_service.get_or_create_session(session_id, user_id)
    
    # Assert
    assert isinstance(result, Session)
    assert result.id == session_id
    assert result.user_id == user_id
    assert result.created_at == created_at
    assert result.last_active_at == created_at
    
    # Verify database was queried twice (SELECT then INSERT)
    assert mock_db.fetchrow.call_count == 2


@pytest.mark.asyncio
async def test_get_or_create_session_no_user_id(session_service, mock_db):
    """Test creating a session without user_id."""
    # Arrange
    session_id = "session_no_user"
    created_at = datetime(2024, 1, 3, 14, 0, 0)
    
    mock_db.fetchrow.side_effect = [
        None,
        {
            'id': session_id,
            'user_id': None,
            'created_at': created_at,
            'last_active_at': created_at
        }
    ]
    
    # Act
    result = await session_service.get_or_create_session(session_id)
    
    # Assert
    assert isinstance(result, Session)
    assert result.id == session_id
    assert result.user_id is None


@pytest.mark.asyncio
async def test_update_last_active(session_service, mock_db):
    """Test updating last_active_at timestamp."""
    # Arrange
    session_id = "session_to_update"
    
    # Act
    await session_service.update_last_active(session_id)
    
    # Assert
    mock_db.execute.assert_called_once()
    call_args = mock_db.execute.call_args
    # Verify session_id is in the call
    assert session_id in call_args[0]
