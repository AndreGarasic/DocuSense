"""
DocuSense - Rate Limiter Configuration

Configures rate limiting using slowapi with IP-based key extraction.
"""
import logging
from functools import lru_cache

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_rate_limit_key(request: Request) -> str:
    """
    Extract rate limit key from request.
    
    Uses IP address as the key for rate limiting.
    """
    return get_remote_address(request)


# Create limiter instance
_limiter = Limiter(
    key_func=_get_rate_limit_key,
    enabled=settings.rate_limit_enabled,
    default_limits=[f"{settings.rate_limit_requests_per_minute}/minute"],
)


@lru_cache()
def get_limiter() -> Limiter:
    """Get the rate limiter instance."""
    return _limiter


def get_rate_limit_string() -> str:
    """Get the rate limit string for decorators."""
    return f"{settings.rate_limit_requests_per_minute}/minute"
