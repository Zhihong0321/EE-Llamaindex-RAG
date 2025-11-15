"""Document service for ingesting and managing documents.

This service handles:
- Document ingestion into LlamaIndex vector store (Requirements 2.1-2.7)
- Document metadata storage in PostgreSQL (Requirement 2.7)
- Document listing and retrieval (Requirements 9.2, 9.3)
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from llama_index.core import VectorStoreIndex, Document
from llama_index.core.schema import TextNode

from app.db.database import Database
from app.models.database import DocumentInfo
from app.logging_config import get_logger
from app.exceptions import DocumentIngestError, DocumentNotFoundError


logger = get_logger(__name__)


class DocumentService:
    """Service for document ingestion and management."""
    
    def __init__(self, db: Database, index: VectorStoreIndex):
        """Initialize DocumentService.
        
        Args:
            db: Database instance for metadata storage
            index: LlamaIndex VectorStoreIndex for vector storage
        """
        self.db = db
        self.index = index
    
    async def ingest(
        self,
        document_id: str,
        text: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Ingest document into vector store and save metadata.
        
        Requirements:
        - 2.1: Expose POST endpoint at "/ingest"
        - 2.2: Create Document object with provided text
        - 2.3: Chunk text into segments suitable for embedding
        - 2.4: Generate embeddings using Embedding_Model
        - 2.5: Store embeddings in Vector_Store
        - 2.6: Insert record into documents table
        - 2.7: Return document_id and status
        
        Args:
            document_id: Unique identifier for the document
            text: Document text content
            title: Optional document title
            source: Optional document source
            metadata: Optional additional metadata
            
        Returns:
            str: The document_id of the ingested document
            
        Raises:
            DocumentIngestError: If ingestion fails
        """
        if metadata is None:
            metadata = {}
        
        logger.info(
            "Starting document ingestion",
            extra={
                "document_id": document_id,
                "title": title,
                "text_length": len(text),
            }
        )
        
        try:
            # Create LlamaIndex Document with metadata (Requirement 2.2)
            # Metadata will be preserved with each chunk
            doc_metadata = {
                "document_id": document_id,
                "title": title,
                "source": source,
                **metadata
            }
            
            # Create Document object
            llama_doc = Document(
                text=text,
                metadata=doc_metadata,
                id_=document_id
            )
            
            logger.debug(
                "Document object created",
                extra={"document_id": document_id}
            )
            
            # Insert into vector index (Requirements 2.3, 2.4, 2.5)
            # LlamaIndex will automatically:
            # - Chunk the text (Requirement 2.3)
            # - Generate embeddings (Requirement 2.4)
            # - Store in vector store (Requirement 2.5)
            self.index.insert(llama_doc)
            
            logger.info(
                "Document inserted into vector index",
                extra={"document_id": document_id}
            )
            
            # Store document metadata in database (Requirement 2.6)
            now = datetime.utcnow()
            
            query = """
                INSERT INTO documents (id, title, source, metadata_json, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """
            
            await self.db.execute(
                query,
                document_id,
                title,
                source,
                json.dumps(metadata),
                now,
                now
            )
            
            logger.info(
                "Document metadata saved to database",
                extra={"document_id": document_id}
            )
            
            return document_id
            
        except Exception as e:
            logger.error(
                "Document ingestion failed",
                extra={"document_id": document_id, "error": str(e)},
                exc_info=True
            )
            raise DocumentIngestError(document_id=document_id, reason=str(e)) from e
    
    async def list_all(self) -> List[DocumentInfo]:
        """Retrieve all documents from database.
        
        Requirement 9.2: Retrieve all records from documents table.
        
        Returns:
            List[DocumentInfo]: List of all documents with metadata
        """
        logger.debug("Listing all documents")
        
        query = """
            SELECT id, title, source, metadata_json, created_at, updated_at
            FROM documents
            ORDER BY created_at DESC
        """
        
        rows = await self.db.fetch(query)
        
        documents = []
        for row in rows:
            doc = DocumentInfo(
                id=row["id"],
                title=row["title"],
                source=row["source"],
                metadata_json=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            documents.append(doc)
        
        logger.info(f"Retrieved {len(documents)} documents")
        
        return documents
    
    async def get_by_id(self, document_id: str) -> Optional[DocumentInfo]:
        """Retrieve specific document by ID.
        
        Requirement 9.3: Return document with fields document_id, title, source, created_at.
        
        Args:
            document_id: Unique document identifier
            
        Returns:
            Optional[DocumentInfo]: Document metadata or None if not found
        """
        logger.debug("Retrieving document by ID", extra={"document_id": document_id})
        
        query = """
            SELECT id, title, source, metadata_json, created_at, updated_at
            FROM documents
            WHERE id = $1
        """
        
        row = await self.db.fetchrow(query, document_id)
        
        if row is None:
            logger.warning("Document not found", extra={"document_id": document_id})
            return None
        
        logger.info("Document retrieved", extra={"document_id": document_id})
        
        return DocumentInfo(
            id=row["id"],
            title=row["title"],
            source=row["source"],
            metadata_json=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
