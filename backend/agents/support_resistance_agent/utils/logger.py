"""
Logging utility for Support/Resistance Agent.

Provides centralized logging configuration for all components.
This helps us track what's happening during level detection.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger instance for a component.
    
    Why we need this:
    - Logging helps us debug issues
    - We can see what the algorithm is doing step by step
    - Helps track errors and warnings
    
    Args:
        name: Logger name (typically __name__ or component name)
        level: Logging level (default: INFO)
              - DEBUG: Very detailed info (for debugging)
              - INFO: General information (normal operation)
              - WARNING: Something unexpected but not critical
              - ERROR: Something went wrong
    
    Returns:
        Configured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Levels detected successfully")
        logger.error("Failed to detect levels", exc_info=True)
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    # This prevents creating multiple handlers for the same logger
    if not logger.handlers:
        logger.setLevel(level or logging.INFO)
        
        # Create console handler - outputs to terminal/console
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level or logging.INFO)
        
        # Create formatter - defines how log messages look
        # Format: [timestamp] [level] [component_name] message
        formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        logger.propagate = False  # Prevent duplicate logs from parent loggers
    
    return logger
