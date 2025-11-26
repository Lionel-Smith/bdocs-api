from functools import wraps
from typing import Callable
import hashlib
import json
from src.cache.redis_client import redis_client


def cache_result(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results in Redis

    Args:
        ttl: Time to live in seconds (default 5 minutes)
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key_data = {
                'function': f"{func.__module__}.{func.__name__}",
                'args': str(args),
                'kwargs': str(sorted(kwargs.items()))
            }
            cache_key_hash = hashlib.md5(
                json.dumps(cache_key_data).encode()
            ).hexdigest()
            cache_key = f"{key_prefix}:{cache_key_hash}" if key_prefix else cache_key_hash

            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached is not None:
                return cached

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_client.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


async def invalidate_cache(key_pattern: str):
    """Helper to invalidate cache keys matching pattern"""
    await redis_client.delete(key_pattern)
