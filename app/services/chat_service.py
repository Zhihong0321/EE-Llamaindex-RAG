"""Chat service for RAG-based conversation generation.

This service orchestrates the RAG chat flow using LlamaIndex components.
It creates chat engines with configurable parameters, manages chat history,
and extracts source information from responses.
"""

from typing import List, Tuple

from llama_index.core import VectorStoreIndex
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI

from app.config import Config
from app.models.responses import Source
from app.logging_config import get_logger
from app.exceptions import ChatGenerationError


logger = get_logger(__name__)


class ChatService:
    """Service for generating RAG-based chat responses.
    
    This service implements Requirements 5.4, 5.5, 5.6, 5.7, and 5.9:
    - 5.4: Perform vector similarity search using user message
    - 5.5: Retrieve top K most similar document chunks
    - 5.6: Provide context and history to Chat_Engine
    - 5.7: Generate response using Chat_Model
    - 5.9: Include source information in response
    """
    
    def __init__(self, index: VectorStoreIndex, llm: OpenAI, config: Config):
        """Initialize ChatService with LlamaIndex components.
        
        Args:
            index: VectorStoreIndex for document retrieval
            llm: OpenAI LLM for response generation
            config: Application configuration
        """
        self.index = index
        self.llm = llm
        self.config = config
    
    async def generate_response(
        self,
        message: str,
        chat_history: List[ChatMessage],
        top_k: int,
        temperature: float,
        session_id: str = "unknown"
    ) -> Tuple[str, List[Source]]:
        """Generate response using RAG with chat history.
        
        This method implements the core RAG chat flow:
        1. Creates a chat engine with configurable parameters (top_k, temperature)
        2. Loads chat history into memory
        3. Performs vector similarity search (Requirement 5.4)
        4. Retrieves top K document chunks (Requirement 5.5)
        5. Provides context and history to chat engine (Requirement 5.6)
        6. Generates response using LLM (Requirement 5.7)
        7. Extracts and formats source information (Requirement 5.9)
        
        Args:
            message: User message to respond to
            chat_history: Previous messages in the conversation
            top_k: Number of document chunks to retrieve (Requirement 5.5)
            temperature: LLM temperature for response generation
            session_id: Session ID for logging purposes
            
        Returns:
            Tuple containing:
            - str: Generated response text
            - List[Source]: Retrieved source documents with metadata
            
        Raises:
            ChatGenerationError: If response generation fails
        """
        try:
            logger.info(
                "Generating chat response",
                extra={
                    "session_id": session_id,
                    "message_length": len(message),
                    "history_length": len(chat_history),
                    "top_k": top_k,
                    "temperature": temperature,
                }
            )
            
            # Create chat memory buffer for conversation history
            memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
            
            # Load chat history into memory (Requirement 5.6)
            for msg in chat_history:
                memory.put(msg)
            
            logger.debug(
                "Chat history loaded into memory",
                extra={"session_id": session_id, "messages": len(chat_history)}
            )
            
            # Create LLM with specified temperature
            # Use the base LLM but update temperature
            # This avoids re-validation of the model name
            llm_with_temp = self.llm
            llm_with_temp.temperature = temperature
            
            # Create chat engine with condense_plus_context mode
            # This mode:
            # - Condenses conversation history into a standalone question
            # - Performs vector similarity search (Requirement 5.4)
            # - Retrieves top_k chunks (Requirement 5.5)
            # - Generates response with context (Requirement 5.6, 5.7)
            chat_engine = self.index.as_chat_engine(
                chat_mode="condense_plus_context",
                memory=memory,
                similarity_top_k=top_k,
                llm=llm_with_temp,
            )
            
            logger.debug(
                "Chat engine created",
                extra={"session_id": session_id, "mode": "condense_plus_context"}
            )
            
            # Generate response
            response = chat_engine.chat(message)
            
            # Extract source nodes and format as Source objects (Requirement 5.9)
            sources = self._extract_sources(response)
            
            logger.info(
                "Chat response generated successfully",
                extra={
                    "session_id": session_id,
                    "response_length": len(str(response)),
                    "sources_count": len(sources),
                }
            )
            
            return str(response), sources
            
        except Exception as e:
            logger.error(
                "Failed to generate chat response",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            raise ChatGenerationError(session_id=session_id, reason=str(e)) from e
    
    def _extract_sources(self, response) -> List[Source]:
        """Extract source nodes from response and format as Source objects.
        
        This method implements Requirement 5.9: Include source information
        with document_id, title, snippet, and score for each retrieved chunk.
        
        Args:
            response: Chat engine response object with source_nodes
            
        Returns:
            List[Source]: Formatted source information
        """
        sources = []
        
        # Check if response has source nodes
        if hasattr(response, 'source_nodes') and response.source_nodes:
            for node in response.source_nodes:
                # Extract metadata
                metadata = node.metadata if hasattr(node, 'metadata') else {}
                document_id = metadata.get('document_id', 'unknown')
                title = metadata.get('title')
                
                # Get text snippet (limit to 200 characters)
                text = node.text if hasattr(node, 'text') else ''
                snippet = text[:200] if text else ''
                
                # Get relevance score
                score = node.score if hasattr(node, 'score') else 0.0
                
                sources.append(Source(
                    document_id=document_id,
                    title=title,
                    snippet=snippet,
                    score=score
                ))
        
        return sources
