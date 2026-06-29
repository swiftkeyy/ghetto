"""
Redis configuration and cache management
"""

from typing import Optional, Any
import json
from redis import asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.core.config import settings


class RedisManager:
    """Redis connection and cache management"""
    
    def __init__(self):
        self._redis: Optional[Redis] = None
    
    async def connect(self) -> None:
        """Initialize Redis connection"""
        try:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            await self._redis.ping()
            print("✅ Redis connected successfully")
        except RedisError as e:
            print(f"❌ Redis connection failed: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            print("✅ Redis disconnected")
    
    @property
    def redis(self) -> Redis:
        """Get Redis client instance"""
        if not self._redis:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._redis
    
    # ============================================================================
    # CACHE OPERATIONS
    # ============================================================================
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            return await self.redis.get(key)
        except RedisError as e:
            print(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None
    ) -> bool:
        """Set key-value with optional expiration (seconds)"""
        try:
            if expire:
                return await self.redis.setex(key, expire, value)
            return await self.redis.set(key, value)
        except RedisError as e:
            print(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            return bool(await self.redis.delete(key))
        except RedisError as e:
            print(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(await self.redis.exists(key))
        except RedisError as e:
            print(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        try:
            return await self.redis.expire(key, seconds)
        except RedisError as e:
            print(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get key TTL in seconds"""
        try:
            return await self.redis.ttl(key)
        except RedisError as e:
            print(f"Redis TTL error for key {key}: {e}")
            return -2
    
    # ============================================================================
    # JSON OPERATIONS
    # ============================================================================
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value by key"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set JSON value with optional expiration"""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, expire)
        except (TypeError, ValueError) as e:
            print(f"JSON serialization error for key {key}: {e}")
            return False
    
    # ============================================================================
    # HASH OPERATIONS
    # ============================================================================
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value"""
        try:
            return await self.redis.hget(name, key)
        except RedisError as e:
            print(f"Redis HGET error for {name}:{key}: {e}")
            return None
    
    async def hset(self, name: str, key: str, value: str) -> bool:
        """Set hash field value"""
        try:
            return bool(await self.redis.hset(name, key, value))
        except RedisError as e:
            print(f"Redis HSET error for {name}:{key}: {e}")
            return False
    
    async def hgetall(self, name: str) -> dict:
        """Get all hash fields"""
        try:
            return await self.redis.hgetall(name)
        except RedisError as e:
            print(f"Redis HGETALL error for {name}: {e}")
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields"""
        try:
            return await self.redis.hdel(name, *keys)
        except RedisError as e:
            print(f"Redis HDEL error for {name}: {e}")
            return 0
    
    # ============================================================================
    # LIST OPERATIONS
    # ============================================================================
    
    async def lpush(self, key: str, *values: str) -> int:
        """Push values to list (left)"""
        try:
            return await self.redis.lpush(key, *values)
        except RedisError as e:
            print(f"Redis LPUSH error for key {key}: {e}")
            return 0
    
    async def rpush(self, key: str, *values: str) -> int:
        """Push values to list (right)"""
        try:
            return await self.redis.rpush(key, *values)
        except RedisError as e:
            print(f"Redis RPUSH error for key {key}: {e}")
            return 0
    
    async def lrange(self, key: str, start: int, end: int) -> list:
        """Get list range"""
        try:
            return await self.redis.lrange(key, start, end)
        except RedisError as e:
            print(f"Redis LRANGE error for key {key}: {e}")
            return []
    
    async def llen(self, key: str) -> int:
        """Get list length"""
        try:
            return await self.redis.llen(key)
        except RedisError as e:
            print(f"Redis LLEN error for key {key}: {e}")
            return 0
    
    # ============================================================================
    # SET OPERATIONS
    # ============================================================================
    
    async def sadd(self, key: str, *members: str) -> int:
        """Add members to set"""
        try:
            return await self.redis.sadd(key, *members)
        except RedisError as e:
            print(f"Redis SADD error for key {key}: {e}")
            return 0
    
    async def smembers(self, key: str) -> set:
        """Get all set members"""
        try:
            return await self.redis.smembers(key)
        except RedisError as e:
            print(f"Redis SMEMBERS error for key {key}: {e}")
            return set()
    
    async def sismember(self, key: str, member: str) -> bool:
        """Check if member in set"""
        try:
            return await self.redis.sismember(key, member)
        except RedisError as e:
            print(f"Redis SISMEMBER error for key {key}: {e}")
            return False
    
    async def srem(self, key: str, *members: str) -> int:
        """Remove members from set"""
        try:
            return await self.redis.srem(key, *members)
        except RedisError as e:
            print(f"Redis SREM error for key {key}: {e}")
            return 0
    
    # ============================================================================
    # RATE LIMITING
    # ============================================================================
    
    async def rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check rate limit for key
        Returns: (is_allowed, remaining_requests)
        """
        try:
            pipe = self.redis.pipeline()
            now = int(await self.redis.time())
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, now - window_seconds)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Count requests in window
            pipe.zcard(key)
            # Set expiration
            pipe.expire(key, window_seconds)
            
            results = await pipe.execute()
            request_count = results[2]
            
            remaining = max(0, max_requests - request_count)
            is_allowed = request_count <= max_requests
            
            return is_allowed, remaining
            
        except RedisError as e:
            print(f"Redis rate limit error for key {key}: {e}")
            return True, max_requests  # Allow on error
    
    # ============================================================================
    # UTILITY
    # ============================================================================
    
    async def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return await self.redis.ping()
        except RedisError:
            return False
    
    async def flushdb(self) -> bool:
        """Clear current database (use with caution!)"""
        try:
            return await self.redis.flushdb()
        except RedisError as e:
            print(f"Redis FLUSHDB error: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> list:
        """Get keys by pattern"""
        try:
            return await self.redis.keys(pattern)
        except RedisError as e:
            print(f"Redis KEYS error for pattern {pattern}: {e}")
            return []


# Global Redis manager instance
redis_manager = RedisManager()


# Dependency for FastAPI
async def get_redis() -> Redis:
    """Get Redis client for dependency injection"""
    return redis_manager.redis
