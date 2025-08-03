"""Cache Manager - Multi-layer cache orchestration"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import structlog

from .memory_cache import MemoryCache
from .redis_cache import RedisCache

logger = structlog.get_logger()


@dataclass
class CacheConfig:
    """Cache configuration"""
    memory_enabled: bool = True
    redis_enabled: bool = True
    memory_ttl: int = 300  # 5 minutes
    redis_ttl: int = 3600  # 1 hour
    

class CacheManager:
    """Multi-layer cache manager with L1 (memory) and L2 (Redis) caching"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        
        # Cache layers
        self.memory_cache: Optional[MemoryCache] = None
        self.redis_cache: Optional[RedisCache] = None
        
        # Statistics
        self._stats = {
            "total_requests": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "l1_hit_ratio": 0.0,
            "l2_hit_ratio": 0.0,
            "overall_hit_ratio": 0.0
        }
    
    async def initialize(
        self,
        memory_cache: Optional[MemoryCache] = None,
        redis_cache: Optional[RedisCache] = None
    ) -> None:
        """Initialize cache layers"""
        try:
            if self.config.memory_enabled:
                self.memory_cache = memory_cache
                if self.memory_cache and not hasattr(self.memory_cache, '_cache'):
                    # Memory cache needs to be initialized
                    pass  # MemoryCache doesn't need async init
                
                logger.info("L1 (memory) cache enabled")
            
            if self.config.redis_enabled:
                self.redis_cache = redis_cache
                if self.redis_cache:
                    await self.redis_cache.initialize()
                
                logger.info("L2 (Redis) cache enabled")
            
            logger.info(
                "Cache manager initialized",
                l1_enabled=self.config.memory_enabled,
                l2_enabled=self.config.redis_enabled
            )
            
        except Exception as e:
            logger.error("Failed to initialize cache manager", error=str(e))
            raise
    
    def _make_cache_key(self, key: str, namespace: str = "default") -> str:
        """Create standardized cache key"""
        return f"{namespace}:{key}"
    
    def _hash_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Create hash for complex query parameters"""
        query_data = {
            "query": query,
            "params": params or {}
        }
        
        # Create deterministic hash
        query_json = json.dumps(query_data, sort_keys=True)
        return hashlib.sha256(query_json.encode()).hexdigest()[:16]
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get value from cache using multi-layer strategy"""
        cache_key = self._make_cache_key(key, namespace)
        self._stats["total_requests"] += 1
        
        try:
            # L1 Cache (Memory) - fastest
            if self.memory_cache:
                value = await self.memory_cache.get(cache_key)
                if value is not None:
                    self._stats["l1_hits"] += 1
                    self._update_hit_ratios()
                    
                    logger.debug(
                        "L1 cache hit",
                        key=key[:50],
                        namespace=namespace
                    )
                    
                    return value
            
            # L2 Cache (Redis) - persistent
            if self.redis_cache:
                value = await self.redis_cache.get(cache_key)
                if value is not None:
                    self._stats["l2_hits"] += 1
                    self._update_hit_ratios()
                    
                    # Populate L1 cache for next time
                    if self.memory_cache:
                        await self.memory_cache.set(
                            cache_key, 
                            value, 
                            ttl_seconds=self.config.memory_ttl
                        )
                    
                    logger.debug(
                        "L2 cache hit",
                        key=key[:50],
                        namespace=namespace
                    )
                    
                    return value
            
            # Cache miss
            self._stats["misses"] += 1
            self._update_hit_ratios()
            
            logger.debug(
                "Cache miss",
                key=key[:50],
                namespace=namespace
            )
            
            return None
            
        except Exception as e:
            logger.error(
                "Cache get error",
                key=key[:50],
                namespace=namespace,
                error=str(e)
            )
            self._stats["misses"] += 1
            self._update_hit_ratios()
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        namespace: str = "default",
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache layers"""
        cache_key = self._make_cache_key(key, namespace)
        
        try:
            # Set in L1 (Memory) cache
            if self.memory_cache:
                memory_ttl = ttl_seconds or self.config.memory_ttl
                await self.memory_cache.set(cache_key, value, memory_ttl)
            
            # Set in L2 (Redis) cache
            if self.redis_cache:
                redis_ttl = ttl_seconds or self.config.redis_ttl
                await self.redis_cache.set(cache_key, value, redis_ttl)
            
            logger.debug(
                "Cache set",
                key=key[:50],
                namespace=namespace,
                ttl_seconds=ttl_seconds
            )
            
        except Exception as e:
            logger.error(
                "Cache set error",
                key=key[:50],
                namespace=namespace,
                error=str(e)
            )
    
    async def delete(self, key: str, namespace: str = "default") -> None:
        """Delete key from all cache layers"""
        cache_key = self._make_cache_key(key, namespace)
        
        try:
            # Delete from L1
            if self.memory_cache:
                await self.memory_cache.delete(cache_key)
            
            # Delete from L2
            if self.redis_cache:
                await self.redis_cache.delete(cache_key)
            
            logger.debug(
                "Cache delete",
                key=key[:50],
                namespace=namespace
            )
            
        except Exception as e:
            logger.error(
                "Cache delete error",
                key=key[:50],
                namespace=namespace,
                error=str(e)
            )
    
    async def invalidate_pattern(
        self, 
        pattern: str, 
        namespace: str = "default"
    ) -> int:
        """Invalidate keys matching pattern"""
        cache_pattern = self._make_cache_key(pattern, namespace)
        deleted_count = 0
        
        try:
            # Redis supports pattern deletion
            if self.redis_cache:
                deleted_count = await self.redis_cache.delete_pattern(cache_pattern)
            
            # For memory cache, we need to get keys and delete individually
            if self.memory_cache:
                keys = await self.memory_cache.keys()
                for key in keys:
                    if cache_pattern.replace("*", "") in key:
                        await self.memory_cache.delete(key)
                        deleted_count += 1
            
            logger.info(
                "Cache pattern invalidation",
                pattern=pattern,
                namespace=namespace,
                deleted_count=deleted_count
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(
                "Cache pattern invalidation error",
                pattern=pattern,
                namespace=namespace,
                error=str(e)
            )
            return 0
    
    async def clear(self, namespace: Optional[str] = None) -> None:
        """Clear cache (optionally by namespace)"""
        try:
            if namespace:
                # Clear specific namespace
                await self.invalidate_pattern("*", namespace)
            else:
                # Clear all
                if self.memory_cache:
                    await self.memory_cache.clear()
                
                if self.redis_cache:
                    await self.redis_cache.clear()
            
            logger.info("Cache cleared", namespace=namespace or "all")
            
        except Exception as e:
            logger.error(
                "Cache clear error",
                namespace=namespace,
                error=str(e)
            )
    
    async def get_or_set(
        self,
        key: str,
        factory_func,
        namespace: str = "default",
        ttl_seconds: Optional[int] = None
    ) -> Any:
        """Get from cache or compute and set"""
        # Try to get from cache first
        value = await self.get(key, namespace)
        if value is not None:
            return value
        
        # Compute value
        try:
            if asyncio.iscoroutinefunction(factory_func):
                value = await factory_func()
            else:
                value = factory_func()
            
            # Store in cache
            await self.set(key, value, namespace, ttl_seconds)
            
            return value
            
        except Exception as e:
            logger.error(
                "Factory function error in get_or_set",
                key=key[:50],
                error=str(e)
            )
            raise
    
    async def get_query_cache(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        namespace: str = "queries"
    ) -> Optional[Any]:
        """Get cached query result"""
        query_hash = self._hash_query(query, params)
        return await self.get(query_hash, namespace)
    
    async def set_query_cache(
        self,
        query: str,
        result: Any,
        params: Optional[Dict[str, Any]] = None,
        namespace: str = "queries",
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Cache query result"""
        query_hash = self._hash_query(query, params)
        await self.set(query_hash, result, namespace, ttl_seconds)
    
    def _update_hit_ratios(self) -> None:
        """Update hit ratio statistics"""
        total = self._stats["total_requests"]
        if total > 0:
            self._stats["l1_hit_ratio"] = self._stats["l1_hits"] / total
            self._stats["l2_hit_ratio"] = self._stats["l2_hits"] / total
            
            total_hits = self._stats["l1_hits"] + self._stats["l2_hits"]
            self._stats["overall_hit_ratio"] = total_hits / total
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {
            "manager": self._stats.copy(),
            "l1_cache": None,
            "l2_cache": None
        }
        
        try:
            if self.memory_cache:
                stats["l1_cache"] = await self.memory_cache.get_stats()
            
            if self.redis_cache:
                stats["l2_cache"] = await self.redis_cache.get_stats()
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all cache layers"""
        health = {
            "status": "healthy",
            "l1_cache": None,
            "l2_cache": None,
            "manager_stats": self._stats
        }
        
        try:
            # Check L1 cache
            if self.memory_cache:
                health["l1_cache"] = await self.memory_cache.health_check()
                if health["l1_cache"]["status"] != "healthy":
                    health["status"] = "degraded"
            
            # Check L2 cache
            if self.redis_cache:
                health["l2_cache"] = await self.redis_cache.health_check()
                if health["l2_cache"]["status"] != "healthy":
                    health["status"] = "degraded"
            
            return health
            
        except Exception as e:
            logger.error("Cache health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self) -> None:
        """Close all cache connections"""
        try:
            if self.memory_cache:
                await self.memory_cache.close()
            
            if self.redis_cache:
                await self.redis_cache.close()
            
            logger.info("Cache manager closed")
            
        except Exception as e:
            logger.error("Error closing cache manager", error=str(e))