"""Redis Cache Implementation - L2 Cache Layer"""

import json
import time
from typing import Any, Dict, List, Optional, Set
import structlog
import redis.asyncio as redis
from redis.asyncio import Redis

logger = structlog.get_logger()


class RedisCache:
    """Redis-based cache for persistent, distributed caching"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        db: int = 0,
        max_connections: int = 20,
        default_ttl_seconds: int = 3600,  # 1 hour
        key_prefix: str = "kb"
    ):
        self.redis_url = redis_url
        self.db = db
        self.max_connections = max_connections
        self.default_ttl_seconds = default_ttl_seconds
        self.key_prefix = key_prefix
        
        # Redis client
        self._redis: Optional[Redis] = None
        
        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
            "hit_ratio": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize Redis connection"""
        try:
            self._redis = await redis.from_url(
                self.redis_url,
                db=self.db,
                max_connections=self.max_connections,
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                health_check_interval=30
            )
            
            # Test connection
            await self._redis.ping()
            
            logger.info(
                "Redis cache initialized",
                url=self.redis_url,
                db=self.db,
                prefix=self.key_prefix
            )
            
        except Exception as e:
            logger.error(
                "Failed to initialize Redis cache",
                error=str(e),
                url=self.redis_url
            )
            raise
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.key_prefix}:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            redis_key = self._make_key(key)
            value = await self._redis.get(redis_key)
            
            if value is None:
                self._stats["misses"] += 1
                self._update_hit_ratio()
                return None
            
            # Deserialize JSON
            try:
                result = json.loads(value)
                self._stats["hits"] += 1
                self._update_hit_ratio()
                
                logger.debug(
                    "Redis cache hit",
                    key=key[:50]
                )
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to deserialize cached value",
                    key=key[:50],
                    error=str(e)
                )
                # Remove corrupted entry
                await self.delete(key)
                self._stats["misses"] += 1
                self._update_hit_ratio()
                return None
                
        except Exception as e:
            logger.error(
                "Redis cache get error",
                key=key[:50],
                error=str(e)
            )
            self._stats["errors"] += 1
            self._stats["misses"] += 1
            self._update_hit_ratio()
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set value in Redis cache"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            redis_key = self._make_key(key)
            ttl = ttl_seconds or self.default_ttl_seconds
            
            # Serialize to JSON
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError) as e:
                logger.error(
                    "Failed to serialize value for caching",
                    key=key[:50],
                    error=str(e)
                )
                return False
            
            # Set with TTL
            result = await self._redis.setex(
                redis_key,
                ttl,
                serialized_value
            )
            
            if result:
                self._stats["sets"] += 1
                logger.debug(
                    "Redis cache set",
                    key=key[:50],
                    ttl_seconds=ttl
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                "Redis cache set error",
                key=key[:50],
                error=str(e)
            )
            self._stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            redis_key = self._make_key(key)
            result = await self._redis.delete(redis_key)
            
            if result > 0:
                self._stats["deletes"] += 1
                logger.debug("Redis cache delete", key=key[:50])
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                "Redis cache delete error",
                key=key[:50],
                error=str(e)
            )
            self._stats["errors"] += 1
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            redis_pattern = self._make_key(pattern)
            keys = await self._redis.keys(redis_pattern)
            
            if keys:
                result = await self._redis.delete(*keys)
                self._stats["deletes"] += result
                logger.debug(
                    "Redis cache pattern delete",
                    pattern=pattern,
                    deleted_count=result
                )
                return result
            
            return 0
            
        except Exception as e:
            logger.error(
                "Redis cache pattern delete error",
                pattern=pattern,
                error=str(e)
            )
            self._stats["errors"] += 1
            return 0
    
    async def clear(self) -> bool:
        """Clear all cache entries with our prefix"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            pattern = self._make_key("*")
            keys = await self._redis.keys(pattern)
            
            if keys:
                result = await self._redis.delete(*keys)
                logger.info(
                    "Redis cache cleared",
                    deleted_count=result
                )
                return True
            
            return True
            
        except Exception as e:
            logger.error(
                "Redis cache clear error",
                error=str(e)
            )
            self._stats["errors"] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            redis_key = self._make_key(key)
            result = await self._redis.exists(redis_key)
            return result > 0
            
        except Exception as e:
            logger.error(
                "Redis cache exists error",
                key=key[:50],
                error=str(e)
            )
            self._stats["errors"] += 1
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL for key (-1 if no TTL, -2 if key doesn't exist)"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            redis_key = self._make_key(key)
            return await self._redis.ttl(redis_key)
            
        except Exception as e:
            logger.error(
                "Redis cache TTL error",
                key=key[:50],
                error=str(e)
            )
            return -2
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern (without prefix)"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            redis_pattern = self._make_key(pattern)
            keys = await self._redis.keys(redis_pattern)
            
            # Remove prefix from keys
            prefix_len = len(self.key_prefix) + 1
            return [key[prefix_len:] for key in keys]
            
        except Exception as e:
            logger.error(
                "Redis cache keys error",
                pattern=pattern,
                error=str(e)
            )
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self._redis:
            return {**self._stats, "status": "disconnected"}
        
        try:
            # Get Redis info
            info = await self._redis.info("memory")
            used_memory_mb = info.get("used_memory", 0) / (1024 * 1024)
            
            # Count our keys
            our_keys = await self.keys()
            
            return {
                **self._stats,
                "status": "connected",
                "used_memory_mb": round(used_memory_mb, 2),
                "our_keys_count": len(our_keys),
                "redis_version": info.get("redis_version", "unknown")
            }
            
        except Exception as e:
            logger.error("Failed to get Redis stats", error=str(e))
            return {**self._stats, "status": "error", "error": str(e)}
    
    def _update_hit_ratio(self) -> None:
        """Update cache hit ratio"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        if total_requests > 0:
            self._stats["hit_ratio"] = self._stats["hits"] / total_requests
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            if not self._redis:
                return {
                    "status": "unhealthy",
                    "error": "Redis client not initialized"
                }
            
            # Test ping
            await self._redis.ping()
            
            # Test basic operations
            test_key = "__health_check__"
            test_value = {"timestamp": time.time(), "status": "ok"}
            
            # Test set/get/delete
            await self.set(test_key, test_value, ttl_seconds=1)
            retrieved = await self.get(test_key)
            await self.delete(test_key)
            
            if retrieved != test_value:
                raise ValueError("Cache operations failed")
            
            stats = await self.get_stats()
            
            return {
                "status": "healthy",
                "operations": "ok",
                "stats": stats
            }
            
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self) -> None:
        """Close Redis connection"""
        try:
            if self._redis:
                await self._redis.close()
                self._redis = None
                logger.info("Redis cache closed")
                
        except Exception as e:
            logger.error("Error closing Redis cache", error=str(e))