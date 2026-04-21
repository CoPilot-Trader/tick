"""
API Key Authentication middleware.

Provides API key validation for all protected endpoints.
Keys are configured via environment variables.
"""

import os
import secrets
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY_QUERY = APIKeyQuery(name="api_key", auto_error=False)

# Generate a default key if none configured (for development)
_default_key = secrets.token_hex(32)


def _get_valid_keys() -> set:
    """Load valid API keys from environment."""
    keys_str = os.getenv("TICK_API_KEYS", "")
    if keys_str:
        return {k.strip() for k in keys_str.split(",") if k.strip()}
    # If no keys configured, allow the default dev key
    return {_default_key}


def _is_auth_enabled() -> bool:
    """Check if auth is enabled. Disabled by default in dev, enabled in prod."""
    return os.getenv("TICK_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")


async def verify_api_key(
    header_key: Optional[str] = Security(API_KEY_HEADER),
    query_key: Optional[str] = Security(API_KEY_QUERY),
) -> str:
    """
    Verify API key from header or query parameter.

    In development (TICK_AUTH_ENABLED=false), all requests pass through.
    In production (TICK_AUTH_ENABLED=true), a valid API key is required.
    """
    if not _is_auth_enabled():
        return "dev-mode"

    api_key = header_key or query_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide via X-API-Key header or api_key query param.",
        )

    valid_keys = _get_valid_keys()
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key
