"""Custom OpenAI LLM wrapper that bypasses model validation for custom API endpoints."""

from typing import Any
from llama_index.llms.openai import OpenAI as LlamaIndexOpenAI


class CustomOpenAI(LlamaIndexOpenAI):
    """Custom OpenAI LLM that bypasses model validation.
    
    This wrapper allows using custom model names with OpenAI-compatible APIs
    that may have models not in the official OpenAI model list.
    """
    
    def __init__(self, **kwargs: Any):
        """Initialize with model validation disabled."""
        # Save the custom model name
        custom_model = kwargs.get("model", "gpt-3.5-turbo")
        
        # Temporarily replace with a valid model name for parent init
        kwargs["model"] = "gpt-3.5-turbo"
        
        # Initialize parent class with valid model
        super().__init__(**kwargs)
        
        # Now override with the actual custom model name
        # This bypasses the validation that happens in __init__
        object.__setattr__(self, "_model", custom_model)
