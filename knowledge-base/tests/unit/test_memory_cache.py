"""Unit tests for MemoryCache"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock
from src.cache.memory_cache import MemoryCache, CacheEntry


@pytest.mark.unit
class TestMemoryCache:
    """Test MemoryCache functionality"""
    
    @pytest.fixture
    def memory_cache(self):
        """Create MemoryCache instance for testing"""
        return MemoryCache(
            max_size_mb=10,
            default_ttl_seconds=300,
            eviction_policy="lru"
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test MemoryCache initialization"""
        cache = MemoryCache(max_size_mb=50, default_ttl_seconds=600)
        
        assert cache.max_size_mb == 50
        assert cache.default_ttl_seconds == 600
        assert cache.eviction_policy == "lru"
        assert len(cache._cache) == 0
        assert cache._stats["hits"] == 0
        assert cache._stats["misses"] == 0
        
        # Cleanup task should be started
        assert cache._cleanup_task is not None
        assert not cache._cleanup_task.done()
        
        # Clean up
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_set_and_get_basic(self, memory_cache):
        """Test basic set and get operations"""
        test_key = "test_key"
        test_value = {"data": "test_value"}
        
        await memory_cache.set(test_key, test_value)
        result = await memory_cache.get(test_key)
        
        assert result == test_value
        assert memory_cache._stats["hits"] == 1
        assert memory_cache._stats["misses"] == 0
        assert memory_cache._stats["hit_ratio"] == 1.0
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, memory_cache):
        """Test getting nonexistent key"""
        result = await memory_cache.get("nonexistent_key")
        
        assert result is None
        assert memory_cache._stats["hits"] == 0
        assert memory_cache._stats["misses"] == 1
        assert memory_cache._stats["hit_ratio"] == 0.0
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, memory_cache):
        """Test TTL expiration"""
        test_key = "expiring_key"
        test_value = "expiring_value"
        
        # Set with 1 second TTL
        await memory_cache.set(test_key, test_value, ttl_seconds=1)
        
        # Should be available immediately
        result = await memory_cache.get(test_key)
        assert result == test_value
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired now
        result = await memory_cache.get(test_key)
        assert result is None
        assert memory_cache._stats["misses"] == 1
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_delete_key(self, memory_cache):
        """Test deleting keys"""
        test_key = "delete_key"
        test_value = "delete_value"
        
        await memory_cache.set(test_key, test_value)
        assert await memory_cache.get(test_key) == test_value
        
        # Delete key
        success = await memory_cache.delete(test_key)
        assert success is True
        
        # Should be gone now
        result = await memory_cache.get(test_key)
        assert result is None
        
        # Deleting nonexistent key
        success = await memory_cache.delete("nonexistent")
        assert success is False
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, memory_cache):
        """Test clearing entire cache"""
        # Add multiple entries
        for i in range(5):
            await memory_cache.set(f"key_{i}", f"value_{i}")
        
        assert memory_cache._stats["entries_count"] == 5
        
        # Clear cache
        await memory_cache.clear()
        
        assert memory_cache._stats["entries_count"] == 0
        assert memory_cache._stats["estimated_size_mb"] == 0.0
        assert len(memory_cache._cache) == 0
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction policy"""
        # Create cache with small size to trigger eviction
        cache = MemoryCache(max_size_mb=1, default_ttl_seconds=300)
        
        # Add many entries to trigger eviction
        for i in range(15):  # This should trigger eviction
            await cache.set(f"key_{i}", f"value_{i}" * 100)  # Larger values
        
        # Should have triggered evictions
        assert cache._stats["evictions"] > 0
        assert cache._stats["entries_count"] < 15
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_entry_access_tracking(self, memory_cache):
        """Test that cache entries track access correctly"""
        test_key = "access_key"
        test_value = "access_value"
        
        await memory_cache.set(test_key, test_value)
        
        # Access multiple times
        for _ in range(3):
            await memory_cache.get(test_key)
        
        # Check internal entry tracking
        entry = memory_cache._cache[test_key]
        assert entry.hit_count == 3
        assert entry.last_accessed > entry.created_at
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_keys_method(self, memory_cache):
        """Test getting all cache keys"""
        # Add some keys
        test_keys = ["key1", "key2", "key3"]
        for key in test_keys:
            await memory_cache.set(key, f"value_{key}")
        
        keys = await memory_cache.keys()
        
        assert isinstance(keys, set)
        assert len(keys) == 3
        for key in test_keys:
            assert key in keys
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_stats_tracking(self, memory_cache):
        """Test statistics tracking"""
        # Initial stats
        stats = await memory_cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["entries_count"] == 0
        
        # Add entry and access it
        await memory_cache.set("test", "value")
        await memory_cache.get("test")  # hit
        await memory_cache.get("missing")  # miss
        
        stats = await memory_cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["entries_count"] == 1
        assert stats["hit_ratio"] == 0.5
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, memory_cache):
        """Test successful health check"""
        health = await memory_cache.health_check()
        
        assert health["status"] == "healthy"
        assert health["operations"] == "ok"
        assert "stats" in health
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, memory_cache):
        """Test health check with simulated failure"""
        # Mock a failure in the set operation
        with patch.object(memory_cache, 'set', side_effect=Exception("Test error")):
            health = await memory_cache.health_check()
            
            assert health["status"] == "unhealthy"
            assert "error" in health
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_cleanup_task_removes_expired_entries(self):
        """Test that cleanup task removes expired entries"""
        cache = MemoryCache(default_ttl_seconds=1)
        
        # Add entries with short TTL
        await cache.set("key1", "value1", ttl_seconds=1)
        await cache.set("key2", "value2", ttl_seconds=1)
        
        assert cache._stats["entries_count"] == 2
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Manually trigger cleanup
        await cache._cleanup_expired_entries()
        
        assert cache._stats["entries_count"] == 0
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, memory_cache):
        """Test concurrent access to cache"""
        async def set_and_get(key_suffix):
            key = f"concurrent_{key_suffix}"
            value = f"value_{key_suffix}"
            await memory_cache.set(key, value)
            result = await memory_cache.get(key)
            return result == value
        
        # Run multiple concurrent operations
        tasks = [set_and_get(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        assert all(results)
        assert memory_cache._stats["entries_count"] == 10
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_large_values(self, memory_cache):
        """Test handling of large values"""
        large_value = "x" * (1024 * 100)  # 100KB string
        
        await memory_cache.set("large_key", large_value)
        result = await memory_cache.get("large_key")
        
        assert result == large_value
        assert memory_cache._stats["estimated_size_mb"] > 0
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_entry_dataclass(self):
        """Test CacheEntry dataclass functionality"""
        current_time = time.time()
        entry = CacheEntry(
            value="test_value",
            expires_at=current_time + 300,
            created_at=current_time
        )
        
        assert entry.value == "test_value"
        assert entry.expires_at == current_time + 300
        assert entry.created_at == current_time
        assert entry.hit_count == 0
        assert entry.last_accessed == 0.0
    
    @pytest.mark.asyncio
    async def test_close_cleanup(self, memory_cache):
        """Test proper cleanup on close"""
        # Add some data
        await memory_cache.set("test", "value")
        
        # Close should clean up
        await memory_cache.close()
        
        # Cleanup task should be cancelled
        assert memory_cache._cleanup_task.cancelled()
        
        # Cache should be cleared
        assert len(memory_cache._cache) == 0
    
    @pytest.mark.asyncio
    async def test_update_existing_entry(self, memory_cache):
        """Test updating existing cache entry"""
        key = "update_key"
        original_value = "original_value"
        updated_value = "updated_value"
        
        # Set original value
        await memory_cache.set(key, original_value)
        assert await memory_cache.get(key) == original_value
        
        # Update with new value
        await memory_cache.set(key, updated_value)
        assert await memory_cache.get(key) == updated_value
        
        # Should still be only one entry
        assert memory_cache._stats["entries_count"] == 1
        
        await memory_cache.close()
    
    @pytest.mark.asyncio
    async def test_size_estimation_update(self, memory_cache):
        """Test that size estimation updates correctly"""
        initial_size = memory_cache._stats["estimated_size_mb"]
        
        # Add entries
        for i in range(5):
            await memory_cache.set(f"key_{i}", f"value_{i}")
        
        # Size should have increased
        assert memory_cache._stats["estimated_size_mb"] > initial_size
        
        # Delete some entries
        await memory_cache.delete("key_0")
        await memory_cache.delete("key_1")
        
        # Size should decrease
        current_size = memory_cache._stats["estimated_size_mb"]
        assert current_size < memory_cache._stats["estimated_size_mb"] or current_size == 0
        
        await memory_cache.close()


@pytest.mark.unit
@pytest.mark.performance
class TestMemoryCachePerformance:
    """Performance tests for MemoryCache"""
    
    @pytest.mark.asyncio
    async def test_high_throughput_operations(self):
        """Test cache performance under high load"""
        cache = MemoryCache(max_size_mb=100, default_ttl_seconds=300)
        
        start_time = time.time()
        
        # Perform many operations
        num_operations = 1000
        for i in range(num_operations):
            await cache.set(f"perf_key_{i}", f"perf_value_{i}")
        
        for i in range(num_operations):
            result = await cache.get(f"perf_key_{i}")
            assert result == f"perf_value_{i}"
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time (adjust based on requirements)
        assert total_time < 5.0  # 5 seconds for 2000 operations
        
        # Check hit ratio
        stats = await cache.get_stats()
        assert stats["hit_ratio"] == 1.0  # All gets should be hits
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_memory_usage_estimation(self):
        """Test memory usage estimation accuracy"""
        cache = MemoryCache(max_size_mb=50, default_ttl_seconds=300)
        
        # Add predictable amount of data
        num_entries = 100
        value_size = "x" * 1000  # 1KB per entry
        
        for i in range(num_entries):
            await cache.set(f"mem_key_{i}", value_size)
        
        stats = await cache.get_stats()
        
        # Should have reasonable size estimation
        assert stats["entries_count"] == num_entries
        assert stats["estimated_size_mb"] > 0
        
        # Rough validation (estimation may not be exact)
        expected_mb = (num_entries * 1000) / (1024 * 1024)  # Convert to MB
        # Allow for 50% variance in estimation
        assert stats["estimated_size_mb"] >= expected_mb * 0.5
        assert stats["estimated_size_mb"] <= expected_mb * 2.0
        
        await cache.close()