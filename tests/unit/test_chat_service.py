"""Unit tests for ChatService."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from llama_index.core.llms import ChatMessage, MessageRole as LlamaMessageRole

from app.services.chat_service import ChatService
from app.models.responses import Source
from app.exceptions import ChatGenerationError


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock()
    config.openai_api_key = "test_api_key"
    config.embedding_model = "text-embedding-3-small"
    config.chat_model = "gpt-4.1-mini"
    return config


@pytest.fixture
def mock_index():
    """Create a mock VectorStoreIndex."""
    index = MagicMock()
    return index


@pytest.fixture
def mock_llm():
    """Create a mock OpenAI LLM."""
    llm = MagicMock()
    llm.model = "gpt-4.1-mini"
    return llm


@pytest.fixture
def chat_service(mock_index, mock_llm, mock_config):
    """Create ChatService instance with mocks."""
    return ChatService(index=mock_index, llm=mock_llm, config=mock_config)


@pytest.mark.asyncio
async def test_generate_response_success(chat_service, mock_index):
    """Test successful response generation."""
    # Arrange
    message = "What is the capital of France?"
    chat_history = [
        ChatMessage(role=LlamaMessageRole.USER, content="Hello"),
        ChatMessage(role=LlamaMessageRole.ASSISTANT, content="Hi there!")
    ]
    top_k = 5
    temperature = 0.7
    session_id = "session_123"
    
    # Mock chat engine and response
    mock_chat_engine = MagicMock()
    mock_response = MagicMock()
    mock_response.__str__ = lambda self: "Paris is the capital of France."
    mock_response.source_nodes = [
        MagicMock(
            metadata={'document_id': 'doc_1', 'title': 'Geography'},
            text='Paris is the capital and largest city of France.',
            score=0.95
        )
    ]
    
    mock_chat_engine.chat.return_value = mock_response
    mock_index.as_chat_engine.return_value = mock_chat_engine
    
    # Act
    with patch('app.services.chat_service.OpenAI') as mock_openai_class:
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance
        
        answer, sources = await chat_service.generate_response(
            message=message,
            chat_history=chat_history,
            top_k=top_k,
            temperature=temperature,
            session_id=session_id
        )
    
    # Assert
    assert answer == "Paris is the capital of France."
    assert len(sources) == 1
    assert isinstance(sources[0], Source)
    assert sources[0].document_id == 'doc_1'
    assert sources[0].title == 'Geography'
    assert sources[0].score == 0.95
    
    # Verify chat engine was created with correct parameters
    mock_index.as_chat_engine.assert_called_once()
    call_kwargs = mock_index.as_chat_engine.call_args[1]
    assert call_kwargs['chat_mode'] == 'condense_plus_context'
    assert call_kwargs['similarity_top_k'] == top_k
    
    # Verify chat was called
    mock_chat_engine.chat.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_generate_response_no_history(chat_service, mock_index):
    """Test response generation with no chat history."""
    # Arrange
    message = "Tell me about Python"
    chat_history = []
    top_k = 3
    temperature = 0.5
    
    mock_chat_engine = MagicMock()
    mock_response = MagicMock()
    mock_response.__str__ = lambda self: "Python is a programming language."
    mock_response.source_nodes = []
    
    mock_chat_engine.chat.return_value = mock_response
    mock_index.as_chat_engine.return_value = mock_chat_engine
    
    # Act
    with patch('app.services.chat_service.OpenAI'):
        answer, sources = await chat_service.generate_response(
            message=message,
            chat_history=chat_history,
            top_k=top_k,
            temperature=temperature
        )
    
    # Assert
    assert answer == "Python is a programming language."
    assert sources == []


@pytest.mark.asyncio
async def test_generate_response_multiple_sources(chat_service, mock_index):
    """Test response generation with multiple source nodes."""
    # Arrange
    message = "What is machine learning?"
    chat_history = []
    
    mock_chat_engine = MagicMock()
    mock_response = MagicMock()
    mock_response.__str__ = lambda self: "Machine learning is a subset of AI."
    mock_response.source_nodes = [
        MagicMock(
            metadata={'document_id': 'doc_1', 'title': 'ML Basics'},
            text='Machine learning is a method of data analysis...',
            score=0.92
        ),
        MagicMock(
            metadata={'document_id': 'doc_2', 'title': 'AI Overview'},
            text='Artificial intelligence encompasses machine learning...',
            score=0.88
        ),
        MagicMock(
            metadata={'document_id': 'doc_3', 'title': None},
            text='Deep learning is a type of machine learning...',
            score=0.85
        )
    ]
    
    mock_chat_engine.chat.return_value = mock_response
    mock_index.as_chat_engine.return_value = mock_chat_engine
    
    # Act
    with patch('app.services.chat_service.OpenAI'):
        answer, sources = await chat_service.generate_response(
            message=message,
            chat_history=chat_history,
            top_k=5,
            temperature=0.3
        )
    
    # Assert
    assert len(sources) == 3
    assert sources[0].document_id == 'doc_1'
    assert sources[0].title == 'ML Basics'
    assert sources[1].document_id == 'doc_2'
    assert sources[2].title is None


@pytest.mark.asyncio
async def test_generate_response_long_snippet(chat_service, mock_index):
    """Test that snippets are truncated to 200 characters."""
    # Arrange
    message = "Test"
    long_text = "A" * 500  # 500 character text
    
    mock_chat_engine = MagicMock()
    mock_response = MagicMock()
    mock_response.__str__ = lambda self: "Response"
    mock_response.source_nodes = [
        MagicMock(
            metadata={'document_id': 'doc_long'},
            text=long_text,
            score=0.9
        )
    ]
    
    mock_chat_engine.chat.return_value = mock_response
    mock_index.as_chat_engine.return_value = mock_chat_engine
    
    # Act
    with patch('app.services.chat_service.OpenAI'):
        answer, sources = await chat_service.generate_response(
            message=message,
            chat_history=[],
            top_k=5,
            temperature=0.3
        )
    
    # Assert
    assert len(sources[0].snippet) == 200


@pytest.mark.asyncio
async def test_generate_response_no_source_nodes(chat_service, mock_index):
    """Test response when no source nodes are returned."""
    # Arrange
    message = "Random question"
    
    mock_chat_engine = MagicMock()
    mock_response = MagicMock()
    mock_response.__str__ = lambda self: "I don't have information about that."
    # Response has no source_nodes attribute
    delattr(type(mock_response), 'source_nodes')
    
    mock_chat_engine.chat.return_value = mock_response
    mock_index.as_chat_engine.return_value = mock_chat_engine
    
    # Act
    with patch('app.services.chat_service.OpenAI'):
        answer, sources = await chat_service.generate_response(
            message=message,
            chat_history=[],
            top_k=5,
            temperature=0.3
        )
    
    # Assert
    assert sources == []


@pytest.mark.asyncio
async def test_generate_response_chat_engine_failure(chat_service, mock_index):
    """Test response generation when chat engine fails."""
    # Arrange
    message = "This will fail"
    session_id = "session_fail"
    
    mock_index.as_chat_engine.side_effect = Exception("Chat engine creation failed")
    
    # Act & Assert
    with pytest.raises(ChatGenerationError) as exc_info:
        with patch('app.services.chat_service.OpenAI'):
            await chat_service.generate_response(
                message=message,
                chat_history=[],
                top_k=5,
                temperature=0.3,
                session_id=session_id
            )
    
    assert session_id in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_response_chat_failure(chat_service, mock_index):
    """Test response generation when chat call fails."""
    # Arrange
    message = "This will fail"
    session_id = "session_chat_fail"
    
    mock_chat_engine = MagicMock()
    mock_chat_engine.chat.side_effect = Exception("Chat generation failed")
    mock_index.as_chat_engine.return_value = mock_chat_engine
    
    # Act & Assert
    with pytest.raises(ChatGenerationError) as exc_info:
        with patch('app.services.chat_service.OpenAI'):
            await chat_service.generate_response(
                message=message,
                chat_history=[],
                top_k=5,
                temperature=0.3,
                session_id=session_id
            )
    
    assert session_id in str(exc_info.value)


def test_extract_sources_with_metadata(chat_service):
    """Test extracting sources with complete metadata."""
    # Arrange
    mock_response = MagicMock()
    mock_response.source_nodes = [
        MagicMock(
            metadata={'document_id': 'doc_1', 'title': 'Test Doc'},
            text='Sample text content',
            score=0.95
        )
    ]
    
    # Act
    sources = chat_service._extract_sources(mock_response)
    
    # Assert
    assert len(sources) == 1
    assert sources[0].document_id == 'doc_1'
    assert sources[0].title == 'Test Doc'
    assert sources[0].snippet == 'Sample text content'
    assert sources[0].score == 0.95


def test_extract_sources_missing_metadata(chat_service):
    """Test extracting sources with missing metadata."""
    # Arrange
    mock_response = MagicMock()
    mock_node = MagicMock()
    mock_node.metadata = {}
    mock_node.text = 'Text without metadata'
    mock_node.score = 0.8
    mock_response.source_nodes = [mock_node]
    
    # Act
    sources = chat_service._extract_sources(mock_response)
    
    # Assert
    assert len(sources) == 1
    assert sources[0].document_id == 'unknown'
    assert sources[0].title is None


def test_extract_sources_no_source_nodes(chat_service):
    """Test extracting sources when response has no source_nodes."""
    # Arrange
    mock_response = MagicMock()
    delattr(type(mock_response), 'source_nodes')
    
    # Act
    sources = chat_service._extract_sources(mock_response)
    
    # Assert
    assert sources == []


def test_extract_sources_empty_source_nodes(chat_service):
    """Test extracting sources when source_nodes is empty."""
    # Arrange
    mock_response = MagicMock()
    mock_response.source_nodes = []
    
    # Act
    sources = chat_service._extract_sources(mock_response)
    
    # Assert
    assert sources == []
