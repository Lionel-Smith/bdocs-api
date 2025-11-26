import redis.asyncio as redis
from typing import Optional, Any
import json
import pickle
from config import RedisDB


class AsyncRedisClient:
    """Async Redis client wrapper"""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        """Initialize Redis connection"""
        self._client = await redis.from_url(
            RedisDB.REDIS_URL,
            encoding="utf-8",
            decode_responses=False,
            socket_connect_timeout=5,
            socket_keepalive=True
        )

    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()

    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """Get value from cache"""
        value = await self._client.get(key)
        if value is None:
            return None

        if deserialize:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value)
        return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True
    ):
        """Set value in cache with optional TTL (seconds)"""
        if serialize:
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)
        else:
            serialized = value

        if ttl:
            await self._client.setex(key, ttl, serialized)
        else:
            await self._client.set(key, serialized)

    async def delete(self, key: str):
        """Delete key from cache"""
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self._client.exists(key) > 0

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        return await self._client.incrby(key, amount)

    async def expire(self, key: str, ttl: int):
        """Set expiration on key"""
        await self._client.expire(key, ttl)


# Global instance
redis_client = AsyncRedisClient()
