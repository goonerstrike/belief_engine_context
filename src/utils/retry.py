"""
Retry logic with exponential backoff for API calls.
"""
import time
import functools
from typing import Callable, Type, Tuple, Optional
from loguru import logger
import config
from .exceptions import RateLimitError

# ============================================================================
# RETRY DECORATOR
# ============================================================================

def retry_with_backoff(
    max_retries: int = None,
    backoff_factor: float = None,
    max_wait: float = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator to retry function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries (default: config.MAX_RETRIES)
        backoff_factor: Backoff multiplier (default: config.RETRY_BACKOFF_FACTOR)
        max_wait: Maximum wait time in seconds (default: config.RETRY_MAX_WAIT)
        exceptions: Tuple of exceptions to catch
        on_retry: Optional callback function called on each retry
    
    Usage:
        @retry_with_backoff(max_retries=3, exceptions=(OpenAIError,))
        def call_api():
            ...
    """
    max_retries = max_retries if max_retries is not None else config.MAX_RETRIES
    backoff_factor = backoff_factor if backoff_factor is not None else config.RETRY_BACKOFF_FACTOR
    max_wait = max_wait if max_wait is not None else config.RETRY_MAX_WAIT
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    retries += 1
                    
                    if retries > max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}"
                        )
                        raise
                    
                    # Calculate wait time with exponential backoff
                    wait_time = min(backoff_factor ** retries, max_wait)
                    
                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} "
                        f"after {wait_time:.1f}s. Error: {e}"
                    )
                    
                    # Call on_retry callback if provided
                    if on_retry:
                        on_retry(retries, e)
                    
                    time.sleep(wait_time)
            
            # Should never reach here
            raise RuntimeError(f"Unexpected retry logic error in {func.__name__}")
        
        return wrapper
    return decorator

# ============================================================================
# OPENAI-SPECIFIC RETRY
# ============================================================================

def retry_openai_call(max_retries: int = None):
    """
    Decorator specifically for OpenAI API calls.
    
    Handles rate limits (429), timeouts, and other OpenAI-specific errors.
    
    Args:
        max_retries: Maximum number of retries
    
    Usage:
        @retry_openai_call(max_retries=3)
        def extract_beliefs(utterance):
            response = openai.ChatCompletion.create(...)
            return response
    """
    max_retries = max_retries if max_retries is not None else config.MAX_RETRIES
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    error_type = type(e).__name__
                    error_msg = str(e)
                    
                    # Check for rate limit (429)
                    is_rate_limit = "429" in error_msg or "rate_limit" in error_msg.lower()
                    
                    # Check for timeout
                    is_timeout = "timeout" in error_msg.lower() or "timed out" in error_msg.lower()
                    
                    # Check for server error (5xx)
                    is_server_error = any(code in error_msg for code in ["500", "502", "503", "504"])
                    
                    # Only retry on specific errors
                    if not (is_rate_limit or is_timeout or is_server_error):
                        logger.error(f"Non-retryable error in {func.__name__}: {error_type}: {error_msg}")
                        raise
                    
                    retries += 1
                    
                    if retries > max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}: {error_type}: {error_msg}"
                        )
                        if is_rate_limit:
                            raise RateLimitError(f"Rate limit exceeded after {max_retries} retries")
                        raise
                    
                    # Calculate wait time (longer for rate limits)
                    if is_rate_limit:
                        wait_time = min(config.RETRY_BACKOFF_FACTOR ** retries * 2, config.RETRY_MAX_WAIT)
                        error_label = "Rate limit"
                    elif is_timeout:
                        wait_time = min(config.RETRY_BACKOFF_FACTOR ** retries, config.RETRY_MAX_WAIT)
                        error_label = "Timeout"
                    else:
                        wait_time = min(config.RETRY_BACKOFF_FACTOR ** retries, config.RETRY_MAX_WAIT)
                        error_label = "Server error"
                    
                    logger.warning(
                        f"{error_label} - Retry {retries}/{max_retries} for {func.__name__} "
                        f"after {wait_time:.1f}s"
                    )
                    
                    time.sleep(wait_time)
            
            raise RuntimeError(f"Unexpected retry logic error in {func.__name__}")
        
        return wrapper
    return decorator

# ============================================================================
# RETRY COUNTER (for quality metrics)
# ============================================================================

class RetryCounter:
    """
    Context manager to count retries for quality metrics.
    
    Usage:
        with RetryCounter() as counter:
            @retry_with_backoff(on_retry=counter.increment)
            def my_function():
                ...
            my_function()
        
        print(f"Total retries: {counter.count}")
    """
    def __init__(self):
        self.count = 0
    
    def increment(self, retry_num: int, error: Exception):
        """Increment retry count."""
        self.count += 1
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "retry_with_backoff",
    "retry_openai_call",
    "RetryCounter",
]

