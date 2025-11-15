"""Unit tests for DocumentService."""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.document_service import DocumentService
from app.models.database import DocumentInfo
from app.exceptions import DocumentIngestError


@pytest.fixture
def mock_db():
    """Create a mock database instance."""
    db = MagicMock()
    db.fetchrow = AsyncMock()
    db.fetch = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_index():
    """Create a mock LlamaIndex VectorStoreIndex."""
    index = MagicMock()
    index.insert = MagicMock()
    return index


@pytest.fixture
def document_service(mock_db, mock_index):
    """Create DocumentService instance with mocks."""
    return DocumentService(db=mock_db, index=mock_index)


@pytest.mark.asyncio
async def test_ingest_document_success(document_service, mock_db, mock_index):
    """Test successful document ingestion."""
    # Arrange
    document_id = "doc_123"
    text = "This is a test document with some content."
    title = "Test Document"
    source = "test_source.txt"
    metadata = {"author": "Test Author"}
    
    # Act
    result = await document_service.ingest(
        document_id=document_id,
        text=text,
        title=title,
        source=source,
        metadata=metadata
    )
    
    # Assert
    assert result == document_id
    
    # Verify index.insert was called
    mock_index.insert.assert_called_once()
    inserted_doc = mock_index.insert.call_args[0][0]
    assert inserted_doc.text == text
    assert inserted_doc.metadata["document_id"] == document_id
    assert inserted_doc.metadata["title"] == title
    assert inserted_doc.metadata["source"] == source
    assert inserted_doc.metadata["author"] == "Test Author"
    
    # Verify database insert was called
    mock_db.execute.assert_called_once()
    call_args = mock_db.execute.call_args[0]
    assert document_id in call_args
    assert title in call_args
    assert source in call_args


@pytest.mark.asyncio
async def test_ingest_document_minimal(document_service, mock_db, mock_index):
    """Test ingesting document with minimal parameters."""
    # Arrange
    document_id = "doc_minimal"
    text = "Minimal document"
    
    # Act
    result = await document_service.ingest(
        document_id=document_id,
        text=text
    )
    
    # Assert
    assert result == document_id
    mock_index.insert.assert_called_once()
    
    # Verify document has None for optional fields
    inserted_doc = mock_index.insert.call_args[0][0]
    assert inserted_doc.metadata["title"] is None
    assert inserted_doc.metadata["source"] is None


@pytest.mark.asyncio
async def test_ingest_document_with_empty_metadata(document_service, mock_db, mock_index):
    """Test ingesting document with no metadata."""
    # Arrange
    document_id = "doc_no_meta"
    text = "Document without metadata"
    
    # Act
    result = await document_service.ingest(
        document_id=document_id,
        text=text,
        metadata=None
    )
    
    # Assert
    assert result == document_id


@pytest.mark.asyncio
async def test_ingest_document_index_failure(document_service, mock_db, mock_index):
    """Test document ingestion when index insert fails."""
    # Arrange
    document_id = "doc_fail"
    text = "This will fail"
    
    mock_index.insert.side_effect = Exception("Index insertion failed")
    
    # Act & Assert
    with pytest.raises(DocumentIngestError) as exc_info:
        await document_service.ingest(document_id=document_id, text=text)
    
    assert document_id in str(exc_info.value)
    mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_document_database_failure(document_service, mock_db, mock_index):
    """Test document ingestion when database insert fails."""
    # Arrange
    document_id = "doc_db_fail"
    text = "Database will fail"
    
    mock_db.execute.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(DocumentIngestError) as exc_info:
        await document_service.ingest(document_id=document_id, text=text)
    
    assert document_id in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_all_documents(document_service, mock_db):
    """Test listing all documents."""
    # Arrange
    created_at_1 = datetime(2024, 1, 1, 12, 0, 0)
    created_at_2 = datetime(2024, 1, 2, 12, 0, 0)
    
    mock_db.fetch.return_value = [
        {
            'id': 'doc_2',
            'title': 'Document 2',
            'source': 'source2.txt',
            'metadata_json': json.dumps({"key": "value2"}),
            'created_at': created_at_2,
            'updated_at': created_at_2
        },
        {
            'id': 'doc_1',
            'title': 'Document 1',
            'source': 'source1.txt',
            'metadata_json': json.dumps({"key": "value1"}),
            'created_at': created_at_1,
            'updated_at': created_at_1
        }
    ]
    
    # Act
    result = await document_service.list_all()
    
    # Assert
    assert len(result) == 2
    assert isinstance(result[0], DocumentInfo)
    assert result[0].id == 'doc_2'
    assert result[0].title == 'Document 2'
    assert result[0].metadata_json == {"key": "value2"}
    assert result[1].id == 'doc_1'
    
    mock_db.fetch.assert_called_once()


@pytest.mark.asyncio
async def test_list_all_documents_empty(document_service, mock_db):
    """Test listing documents when none exist."""
    # Arrange
    mock_db.fetch.return_value = []
    
    # Act
    result = await document_service.list_all()
    
    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_list_all_documents_null_metadata(document_service, mock_db):
    """Test listing documents with null metadata."""
    # Arrange
    created_at = datetime(2024, 1, 1, 12, 0, 0)
    
    mock_db.fetch.return_value = [
        {
            'id': 'doc_null_meta',
            'title': 'Document',
            'source': 'source.txt',
            'metadata_json': None,
            'created_at': created_at,
            'updated_at': created_at
        }
    ]
    
    # Act
    result = await document_service.list_all()
    
    # Assert
    assert len(result) == 1
    assert result[0].metadata_json == {}


@pytest.mark.asyncio
async def test_get_by_id_found(document_service, mock_db):
    """Test getting a document by ID when it exists."""
    # Arrange
    document_id = "doc_exists"
    created_at = datetime(2024, 1, 1, 12, 0, 0)
    updated_at = datetime(2024, 1, 2, 12, 0, 0)
    
    mock_db.fetchrow.return_value = {
        'id': document_id,
        'title': 'Existing Document',
        'source': 'existing.txt',
        'metadata_json': json.dumps({"status": "active"}),
        'created_at': created_at,
        'updated_at': updated_at
    }
    
    # Act
    result = await document_service.get_by_id(document_id)
    
    # Assert
    assert result is not None
    assert isinstance(result, DocumentInfo)
    assert result.id == document_id
    assert result.title == 'Existing Document'
    assert result.source == 'existing.txt'
    assert result.metadata_json == {"status": "active"}
    assert result.created_at == created_at
    assert result.updated_at == updated_at
    
    mock_db.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id_not_found(document_service, mock_db):
    """Test getting a document by ID when it doesn't exist."""
    # Arrange
    document_id = "doc_not_exists"
    mock_db.fetchrow.return_value = None
    
    # Act
    result = await document_service.get_by_id(document_id)
    
    # Assert
    assert result is None
    mock_db.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id_null_metadata(document_service, mock_db):
    """Test getting a document with null metadata."""
    # Arrange
    document_id = "doc_null"
    created_at = datetime(2024, 1, 1, 12, 0, 0)
    
    mock_db.fetchrow.return_value = {
        'id': document_id,
        'title': 'Document',
        'source': None,
        'metadata_json': None,
        'created_at': created_at,
        'updated_at': created_at
    }
    
    # Act
    result = await document_service.get_by_id(document_id)
    
    # Assert
    assert result is not None
    assert result.metadata_json == {}
    assert result.source is None
