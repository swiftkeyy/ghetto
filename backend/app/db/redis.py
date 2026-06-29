"""
GHETTO VPN - Redis Connection Manager
Handles Redis connections for caching, rate limiting, and sessions
"""

from typing import Optional, Any, Union
import json
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool

from app.core.config import settings


# ============================================
# Redis Connection Pool
# ============================================

redis_pool: Optional[ConnectionPool] = None
redis_client: Optional[Redis] = None


async def init_redis() -> Redis:
    """
    Initialize Redis connection pool.
    
    Returns:
        Redis client instance
    """
    global redis_pool, redis_client
    
    redis_pool = ConnectionPool.from_url(
        settings.redis_url,
        max_connections=settings.redis_pool_size,
        decode_responses=True,
    )
    
    redis_client = Redis(connection_pool=redis_pool)
    
    return redis_client


async def close_redis() -> None:
    """
    Close Redis connections gracefully.
    """
    global redis_client, redis_pool
    
    if redis_client:
        await redis_client.close()
    
    if redis_pool:
        await redis_pool.disconnect()


async def get_redis() -> Redis:
    """
    Get Redis client instance.
    
    Returns:
        Redis client
    """
    global redis_client
    
    if redis_client is None:
        redis_client = await init_redis()
    
    return redis_client


# ============================================
# Redis Cache Utilities
# ============================================

class RedisCache:
    """Redis cache wrapper with JSON serialization"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            expire: TTL in seconds (optional)
            
        Returns:
            True if successful
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        if expire:
            return await self.redis.setex(key, expire, value)
        return await self.redis.set(key, value)
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        return await self.redis.delete(key) > 0
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists
        
        Args:
            key: Cache key
            
        Returns:
            True if exists
        """
        return await self.redis.exists(key) > 0
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment counter
        
        Args:
            key: Counter key
            amount: Increment amount
            
        Returns:
            New counter value
        """
        return await self.redis.incrby(key, amount)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on key
        
        Args:
            key: Cache key
            seconds: TTL in seconds
            
        Returns:
            True if successful
        """
        return await self.redis.expire(key, seconds)


# ============================================
# Rate Limiting
# ============================================

class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window: int
    ) -> bool:
        """
        Check if rate limit is exceeded
        
        Args:
            key: Rate limit key (e.g., user_id, ip_address)
            max_requests: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            True if rate limited, False otherwise
        """
        current = await self.redis.get(f"ratelimit:{key}")
        
        if current is None:
            await self.redis.setex(f"ratelimit:{key}", window, 1)
            return False
        
        if int(current) >= max_requests:
            return True
        
        await self.redis.incr(f"ratelimit:{key}")
        return False
    
    async def get_remaining(
        self,
        key: str,
        max_requests: int
    ) -> int:
        """
        Get remaining requests in current window
        
        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed
            
        Returns:
            Number of remaining requests
        """
        current = await self.redis.get(f"ratelimit:{key}")
        if current is None:
            return max_requests
        return max(0, max_requests - int(current))


# ============================================
# Session Management
# ============================================

class SessionStore:
    """Redis-based session storage"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "session:user:"
    
    async def get_session(self, user_id: int) -> Optional[dict]:
        """
        Get user session data
        
        Args:
            user_id: User ID
            
        Returns:
            Session data or None
        """
        key = f"{self.prefix}{user_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set_session(
        self,
        user_id: int,
        data: dict,
        expire: int = 86400
    ) -> bool:
        """
        Set user session data
        
        Args:
            user_id: User ID
            data: Session data
            expire: Session TTL in seconds (default 24h)
            
        Returns:
            True if successful
        """
        key = f"{self.prefix}{user_id}"
        return await self.redis.setex(key, expire, json.dumps(data))
    
    async def delete_session(self, user_id: int) -> bool:
        """
        Delete user session
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted
        """
        key = f"{self.prefix}{user_id}"
        return await self.redis.delete(key) > 0
    
    async def update_last_activity(self, user_id: int) -> bool:
        """
        Update last activity timestamp
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        key = f"{self.prefix}{user_id}:last_activity"
        return await self.redis.set(key, str(int(aioredis.util.time())))


# ============================================
# Distributed Locks
# ============================================

class DistributedLock:
    """Redis-based distributed lock"""
    
    def __init__(self, redis_client: Redis, key: str, timeout: int = 10):
        self.redis = redis_client
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.identifier = None
    
    async def acquire(self) -> bool:
        """
        Acquire lock
        
        Returns:
            True if acquired, False otherwise
        """
        import uuid
        self.identifier = str(uuid.uuid4())
        
        return await self.redis.set(
            self.key,
            self.identifier,
            nx=True,
            ex=self.timeout
        )
    
    async def release(self) -> bool:
        """
        Release lock
        
        Returns:
            True if released, False otherwise
        """
        if self.identifier is None:
            return False
        
        # Use Lua script to ensure atomic release
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = await self.redis.eval(lua_script, 1, self.key, self.identifier)
        return result == 1


@asynccontextmanager
async def redis_lock(key: str, timeout: int = 10):
    """
    Context manager for distributed lock
    
    Usage:
        async with redis_lock("payment:123"):
            # Critical section
            pass
    
    Args:
        key: Lock key
        timeout: Lock timeout in seconds
    """
    redis = await get_redis()
    lock = DistributedLock(redis, key, timeout)
    
    acquired = await lock.acquire()
    if not acquired:
        raise RuntimeError(f"Failed to acquire lock: {key}")
    
    try:
        yield
    finally:
        await lock.release()


# ============================================
# Health Check
# ============================================

async def check_redis_connection() -> bool:
    """
    Check if Redis connection is healthy
    
    Returns:
        True if healthy, False otherwise
    """
    try:
        redis = await get_redis()
        await redis.ping()
        return True
    except Exception:
        return False
