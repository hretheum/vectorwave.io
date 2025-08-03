"""In-Memory Cache Implementation - L1 Cache Layer"""

import asyncio
import time
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass
from collections import OrderedDict
import structlog

logger = structlog.get_logger()


@dataclass
class CacheEntry:
    """Cache entry with TTL and metadata"""
    value: Any
    expires_at: float
    created_at: float
    hit_count: int = 0
    last_accessed: float = 0.0


class MemoryCache:
    """High-performance in-memory cache with TTL and LRU eviction"""
    
    def __init__(
        self,
        max_size_mb: int = 512,
        default_ttl_seconds: int = 300,  # 5 minutes
        eviction_policy: str = "lru"
    ):
        self.max_size_mb = max_size_mb
        self.default_ttl_seconds = default_ttl_seconds
        self.eviction_policy = eviction_policy
        
        # Cache storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        
        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "entries_count": 0,
            "estimated_size_mb": 0.0,
            "hit_ratio": 0.0
        }
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self) -> None:
        """Start background cleanup task for expired entries"""
        async def cleanup_expired():
            while True:
                try:
                    await asyncio.sleep(60)  # Check every minute
                    await self._cleanup_expired_entries()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Cache cleanup error", error=str(e))
        
        self._cleanup_task = asyncio.create_task(cleanup_expired())
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats["misses"] += 1
                self._update_hit_ratio()
                return None
            
            # Check if expired
            current_time = time.time()
            if current_time > entry.expires_at:
                del self._cache[key]
                self._stats["misses"] += 1
                self._stats["entries_count"] -= 1
                self._update_hit_ratio()
                return None
            
            # Update access stats
            entry.hit_count += 1
            entry.last_accessed = current_time
            
            # Move to end (most recently used) for LRU
            self._cache.move_to_end(key)
            
            self._stats["hits"] += 1
            self._update_hit_ratio()
            
            logger.debug(
                "Cache hit",
                key=key[:50],  # Truncate for logging
                hit_count=entry.hit_count
            )
            
            return entry.value
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache with optional TTL"""
        ttl = ttl_seconds or self.default_ttl_seconds
        current_time = time.time()
        expires_at = current_time + ttl
        
        async with self._lock:
            # Check if we need to evict entries
            await self._ensure_space_available()
            
            # Create or update entry
            if key in self._cache:
                # Update existing entry
                entry = self._cache[key]
                entry.value = value
                entry.expires_at = expires_at
                entry.last_accessed = current_time
            else:
                # Create new entry
                entry = CacheEntry(
                    value=value,
                    expires_at=expires_at,
                    created_at=current_time,
                    last_accessed=current_time
                )
                self._cache[key] = entry
                self._stats["entries_count"] += 1
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            # Update size estimation
            self._update_size_estimation()
            
            logger.debug(
                "Cache set",
                key=key[:50],
                ttl_seconds=ttl,
                entries_count=self._stats["entries_count"]
            )
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["entries_count"] -= 1
                self._update_size_estimation()
                logger.debug("Cache delete", key=key[:50])
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            self._stats["entries_count"] = 0
            self._stats["estimated_size_mb"] = 0.0
            logger.info("Cache cleared")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            return self._stats.copy()
    
    async def _ensure_space_available(self) -> None:
        """Ensure there's space available, evict if necessary"""
        # Simple size check based on entry count and estimated size
        if (self._stats["estimated_size_mb"] > self.max_size_mb or
            len(self._cache) > 10000):  # Max 10k entries as safety
            await self._evict_entries()
    
    async def _evict_entries(self) -> None:
        """Evict entries based on eviction policy"""
        if self.eviction_policy == "lru":
            # Remove least recently used entries (first in OrderedDict)
            evict_count = max(1, len(self._cache) // 10)  # Evict 10%
            
            for _ in range(evict_count):
                if not self._cache:
                    break
                
                key, _ = self._cache.popitem(last=False)  # Remove first (oldest)
                self._stats["evictions"] += 1
                self._stats["entries_count"] -= 1
                
                logger.debug("Cache eviction", key=key[:50], policy="lru")
        
        self._update_size_estimation()
    
    async def _cleanup_expired_entries(self) -> None:
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = []
        
        async with self._lock:
            for key, entry in self._cache.items():
                if current_time > entry.expires_at:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._stats["entries_count"] -= 1
        
        if expired_keys:
            self._update_size_estimation()
            logger.debug(
                "Cleaned up expired entries",
                count=len(expired_keys)
            )
    
    def _update_size_estimation(self) -> None:
        """Update estimated cache size (rough calculation)"""
        # Very rough estimation: assume average entry is 5KB
        avg_entry_size_kb = 5
        self._stats["estimated_size_mb"] = (
            self._stats["entries_count"] * avg_entry_size_kb
        ) / 1024
    
    def _update_hit_ratio(self) -> None:
        """Update cache hit ratio"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        if total_requests > 0:
            self._stats["hit_ratio"] = self._stats["hits"] / total_requests
    
    async def keys(self) -> Set[str]:
        """Get all cache keys"""
        async with self._lock:
            return set(self._cache.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test basic operations
            test_key = "__health_check__"
            test_value = "ok"
            
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
            logger.error("Memory cache health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self) -> None:
        """Close cache and cleanup resources"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            await self.clear()
            logger.info("Memory cache closed")
            
        except Exception as e:
            logger.error("Error closing memory cache", error=str(e))