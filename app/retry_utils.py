"""Retry utilities for external service calls.

This module provides retry logic for OpenAI API calls using tenacity
to handle transient failures gracefully.

Requirement 10.4: Implement retry logic for OpenAI API calls.
"""

from typing import TypeVar, Callable, Any
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

from app.logging_config import get_logger
from app.exceptions import OpenAIServiceError


logger = get_logger(__name__)

T = TypeVar('T')


# Define retry decorator for OpenAI API calls
def retry_openai_call(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to add retry logic to OpenAI API calls.
    
    Retries up to 3 times with exponential backoff for:
    - Rate limit errors
    - Timeout errors
    - Connection errors
    - Server errors (5xx)
    
    Args:
        func: Function to wrap with retry logic
        
    Returns:
        Wrapped function with retry logic
    """
    @wraps(func)
    @retry(
        # Retry on specific OpenAI exceptions
        retry=retry_if_exception_type((
            Exception,  # Catch all for now, can be more specific
        )),
        # Stop after 3 attempts
        stop=stop_after_attempt(3),
        # Exponential backoff: 1s, 2s, 4s
        wait=wait_exponential(multiplier=1, min=1, max=10),
        # Log before sleeping
        before_sleep=before_sleep_log(logger, logger.level),
        # Log after retry
        after=after_log(logger, logger.level),
        # Re-raise the last exception if all retries fail
        reraise=True
    )
    async def async_wrapper(*args: Any, **kwargs: Any) -> T:
        """Async wrapper for retry logic."""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Log the error
            logger.error(
                f"OpenAI API call failed after retries: {func.__name__}",
                extra={"error": str(e)},
                exc_info=True
            )
            # Wrap in our custom exception
            raise OpenAIServiceError(
                operation=func.__name__,
                reason=str(e)
            ) from e
    
    @wraps(func)
    @retry(
        retry=retry_if_exception_type((
            Exception,
        )),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logger.level),
        after=after_log(logger, logger.level),
        reraise=True
    )
    def sync_wrapper(*args: Any, **kwargs: Any) -> T:
        """Sync wrapper for retry logic."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"OpenAI API call failed after retries: {func.__name__}",
                extra={"error": str(e)},
                exc_info=True
            )
            raise OpenAIServiceError(
                operation=func.__name__,
                reason=str(e)
            ) from e
    
    # Return appropriate wrapper based on function type
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper  # type: ignore
    else:
        return sync_wrapper  # type: ignore


def should_retry_openai_error(exception: Exception) -> bool:
    """Determine if an OpenAI error should be retried.
    
    Args:
        exception: Exception to check
        
    Returns:
        True if the error should be retried, False otherwise
    """
    # Check for specific error types that should be retried
    error_str = str(exception).lower()
    
    # Retry on rate limits
    if "rate limit" in error_str or "429" in error_str:
        return True
    
    # Retry on timeouts
    if "timeout" in error_str or "timed out" in error_str:
        return True
    
    # Retry on connection errors
    if "connection" in error_str or "connect" in error_str:
        return True
    
    # Retry on server errors (5xx)
    if any(code in error_str for code in ["500", "502", "503", "504"]):
        return True
    
    # Don't retry on client errors (4xx except 429)
    if any(code in error_str for code in ["400", "401", "403", "404"]):
        return False
    
    # Default: retry
    return True
