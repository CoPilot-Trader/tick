"""
Retry utility with exponential backoff for API requests.

Provides retry logic for handling transient API failures.
"""

import time
import logging
from typing import Callable, TypeVar, Optional, List
from functools import wraps

T = TypeVar('T')
logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exceptions: Tuple of exceptions to catch and retry (default: all exceptions)
        on_retry: Optional callback function called on each retry (exception, attempt_number)
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        def fetch_news():
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        current_delay = min(delay, max_delay)
                        
                        # Log retry attempt
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                            f"Retrying in {current_delay:.2f} seconds..."
                        )
                        
                        # Call optional retry callback
                        if on_retry:
                            try:
                                on_retry(e, attempt + 1)
                            except Exception:
                                pass  # Don't fail on callback errors
                        
                        # Wait before retry
                        time.sleep(current_delay)
                        
                        # Increase delay for next retry
                        delay *= backoff_factor
                    else:
                        # Final attempt failed
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {str(e)}"
                        )
                        raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def retry_api_request(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0
) -> T:
    """
    Retry an API request function with exponential backoff.
    
    This is a convenience function for retrying API calls without using decorators.
    
    Args:
        func: Function to retry (should be a callable that makes an API request)
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Backoff multiplier (default: 2.0)
        max_delay: Maximum delay in seconds (default: 60.0)
    
    Returns:
        Result from the function
    
    Raises:
        Last exception if all retries fail
    
    Example:
        result = retry_api_request(
            lambda: requests.get(url, timeout=30),
            max_retries=3
        )
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except (ConnectionError, TimeoutError, Exception) as e:
            last_exception = e
            
            if attempt < max_retries:
                current_delay = min(delay, max_delay)
                logger.warning(
                    f"API request failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                    f"Retrying in {current_delay:.2f} seconds..."
                )
                time.sleep(current_delay)
                delay *= backoff_factor
            else:
                logger.error(f"API request failed after {max_retries + 1} attempts: {str(e)}")
                raise
    
    if last_exception:
        raise last_exception

