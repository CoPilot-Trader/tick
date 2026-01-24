"""
Retry utility with exponential backoff for data loading and API requests.

Why we need this:
- When loading data from Data Agent or yfinance, network issues might occur
- API rate limits might cause temporary failures
- Exponential backoff: wait 1s, then 2s, then 4s, etc. (gives server time to recover)
"""

import time
import logging
from typing import Callable, TypeVar, Optional
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
    
    How it works:
    1. Try to run the function
    2. If it fails, wait a bit (initial_delay)
    3. Try again
    4. If it fails again, wait longer (delay * backoff_factor)
    5. Repeat until max_retries reached
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
                       - 1st retry: wait 1s
                       - 2nd retry: wait 2s
                       - 3rd retry: wait 4s
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exceptions: Tuple of exceptions to catch and retry (default: all exceptions)
        on_retry: Optional callback function called on each retry
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        def load_data():
            # This will retry up to 3 times if it fails
            return fetch_ohlcv_data()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Try to execute the function
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
                        
                        # Increase delay for next retry (exponential backoff)
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
