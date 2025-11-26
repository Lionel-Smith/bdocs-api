from quart import request, jsonify
from functools import wraps
from typing import Optional
import time
from src.cache.redis_client import redis_client
from config import RateLimiter


def parse_rate_limit(rate_string: str) -> tuple[int, int]:
    """
    Parse rate limit string like '100/minute' or '1000/hour'
    Returns (max_requests, window_seconds)
    """
    count, period = rate_string.split('/')
    count = int(count)

    period_map = {
        'second': 1,
        'minute': 60,
        'hour': 3600,
        'day': 86400
    }

    window = period_map.get(period.lower(), 60)
    return count, window


async def check_rate_limit(
    identifier: str,
    max_requests: int,
    window_seconds: int
) -> bool:
    """
    Check if rate limit is exceeded using sliding window

    Args:
        identifier: Unique identifier (e.g., user_id, IP address)
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds

    Returns:
        True if request is allowed, False if rate limit exceeded
    """
    key = f"rate_limit:{identifier}"
    current_time = int(time.time())
    window_start = current_time - window_seconds

    # Use Redis sorted set for sliding window
    pipe = redis_client._client.pipeline()

    # Remove old entries
    pipe.zremrangebyscore(key, 0, window_start)

    # Add current request
    pipe.zadd(key, {str(current_time): current_time})

    # Count requests in window
    pipe.zcard(key)

    # Set expiration
    pipe.expire(key, window_seconds)

    results = await pipe.execute()
    request_count = results[2]

    return request_count <= max_requests


def rate_limit(rate: Optional[str] = None):
    """
    Decorator to apply rate limiting to routes

    Usage:
        @rate_limit("10/minute")
        async def my_route():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Use provided rate or default
            rate_string = rate or RateLimiter.default
            max_requests, window = parse_rate_limit(rate_string)

            # Get identifier (IP address or user ID)
            identifier = request.remote_addr

            # TODO: Extract user_id from JWT token when available
            # if hasattr(request, 'user_id'):
            #     identifier = f"user:{request.user_id}"

            # Check rate limit
            allowed = await check_rate_limit(identifier, max_requests, window)

            if not allowed:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {max_requests} requests per {window} seconds"
                }), 429

            return await func(*args, **kwargs)
        return wrapper
    return decorator
