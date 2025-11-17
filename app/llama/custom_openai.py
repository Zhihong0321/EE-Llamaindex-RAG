"""Custom OpenAI LLM wrapper that bypasses model validation for custom API endpoints."""

from typing import Any, Optional
from llama_index.llms.openai import OpenAI as LlamaIndexOpenAI
from openai import OpenAI as OpenAIClient


class CustomOpenAI(LlamaIndexOpenAI):
    """Custom OpenAI LLM that bypasses model validation.
    
    This wrapper allows using custom model names with OpenAI-compatible APIs
    that may have models not in the official OpenAI model list.
    """
    
    def __init__(self, **kwargs: Any):
        """Initialize with model validation disabled."""
        # Extract our custom parameters
        api_base = kwargs.pop("api_base", None)
        
        # Initialize parent without validation
        # We'll set the model name directly without going through validation
        model = kwargs.get("model", "gpt-3.5-turbo")
        
        # Create the underlying OpenAI client directly
        client_kwargs = {
            "api_key": kwargs.get("api_key"),
        }
        
        if api_base:
            client_kwargs["base_url"] = api_base
        
        # Initialize parent class
        super().__init__(**kwargs)
        
        # Override the client with our custom one
        self._client = OpenAIClient(**client_kwargs)
        self._aclient = None  # Will be created on demand
        
        # Force set the model name without validation
        self._model = model
    
    @property
    def model(self) -> str:
        """Get model name."""
        return self._model
    
    @model.setter
    def model(self, value: str) -> None:
        """Set model name without validation."""
        self._model = value
