"""Unit tests for CacheManager"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.cache import CacheManager, CacheConfig, MemoryCache, RedisCache


class TestCacheManager:
    """Test CacheManager functionality"""
    
    @pytest.fixture
    def cache_config(self):
        """Create cache configuration for testing"""
        return CacheConfig(
            memory_enabled=True,
            redis_enabled=True,
            memory_ttl=300,
            redis_ttl=3600
        )
    
    @pytest.fixture
    def mock_memory_cache(self):
        """Create mock memory cache"""
        mock = AsyncMock(spec=MemoryCache)
        mock.get.return_value = None
        mock.set.return_value = None
        mock.delete.return_value = True
        mock.clear.return_value = None
        mock.get_stats.return_value = {
            "hits": 10,
            "misses": 5,
            "hit_ratio": 0.67
        }
        mock.health_check.return_value = {"status": "healthy"}
        return mock
    
    @pytest.fixture
    def mock_redis_cache(self):
        """Create mock Redis cache"""
        mock = AsyncMock(spec=RedisCache)
        mock.initialize.return_value = None
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.clear.return_value = True
        mock.get_stats.return_value = {
            "hits": 20,
            "misses": 3,
            "hit_ratio": 0.87
        }
        mock.health_check.return_value = {"status": "healthy"}
        return mock
    
    @pytest.fixture
    async def cache_manager(self, cache_config, mock_memory_cache, mock_redis_cache):
        """Create initialized CacheManager for testing"""
        manager = CacheManager(cache_config)
        await manager.initialize(mock_memory_cache, mock_redis_cache)
        return manager
    
    @pytest.mark.asyncio
    async def test_initialization(self, cache_config, mock_memory_cache, mock_redis_cache):
        """Test CacheManager initialization"""
        manager = CacheManager(cache_config)
        
        await manager.initialize(mock_memory_cache, mock_redis_cache)
        
        assert manager.memory_cache == mock_memory_cache
        assert manager.redis_cache == mock_redis_cache
        mock_redis_cache.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_miss_both_layers(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test cache miss on both L1 and L2"""
        # Both caches return None (miss)
        mock_memory_cache.get.return_value = None
        mock_redis_cache.get.return_value = None
        
        result = await cache_manager.get("test_key")
        
        assert result is None
        mock_memory_cache.get.assert_called_once_with("default:test_key")
        mock_redis_cache.get.assert_called_once_with("default:test_key")
        
        # Check stats
        assert cache_manager._stats["total_requests"] == 1
        assert cache_manager._stats["misses"] == 1
        assert cache_manager._stats["l1_hits"] == 0
        assert cache_manager._stats["l2_hits"] == 0
    
    @pytest.mark.asyncio
    async def test_l1_cache_hit(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test L1 (memory) cache hit"""
        test_value = {"data": "test"}
        mock_memory_cache.get.return_value = test_value
        
        result = await cache_manager.get("test_key")
        
        assert result == test_value
        mock_memory_cache.get.assert_called_once_with("default:test_key")
        # Redis should not be called on L1 hit
        mock_redis_cache.get.assert_not_called()
        
        # Check stats
        assert cache_manager._stats["l1_hits"] == 1
        assert cache_manager._stats["l2_hits"] == 0
        assert cache_manager._stats["overall_hit_ratio"] == 1.0
    
    @pytest.mark.asyncio
    async def test_l2_cache_hit(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test L2 (Redis) cache hit with L1 population"""
        test_value = {"data": "test"}
        mock_memory_cache.get.return_value = None  # L1 miss
        mock_redis_cache.get.return_value = test_value  # L2 hit
        
        result = await cache_manager.get("test_key")
        
        assert result == test_value
        mock_memory_cache.get.assert_called_once_with("default:test_key")
        mock_redis_cache.get.assert_called_once_with("default:test_key")
        
        # L1 should be populated for next time
        mock_memory_cache.set.assert_called_once_with(
            "default:test_key", test_value, 300
        )
        
        # Check stats
        assert cache_manager._stats["l1_hits"] == 0
        assert cache_manager._stats["l2_hits"] == 1
        assert cache_manager._stats["overall_hit_ratio"] == 1.0
    
    @pytest.mark.asyncio
    async def test_set_both_layers(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test setting value in both cache layers"""
        test_value = {"data": "test"}
        
        await cache_manager.set("test_key", test_value)
        
        # Both caches should be updated
        mock_memory_cache.set.assert_called_once_with(
            "default:test_key", test_value, 300
        )
        mock_redis_cache.set.assert_called_once_with(
            "default:test_key", test_value, 3600
        )
    
    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test setting value with custom TTL"""
        test_value = {"data": "test"}
        custom_ttl = 1800
        
        await cache_manager.set("test_key", test_value, ttl_seconds=custom_ttl)
        
        # Both caches should use custom TTL
        mock_memory_cache.set.assert_called_once_with(
            "default:test_key", test_value, custom_ttl
        )
        mock_redis_cache.set.assert_called_once_with(
            "default:test_key", test_value, custom_ttl
        )
    
    @pytest.mark.asyncio
    async def test_delete_both_layers(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test deleting from both cache layers"""
        await cache_manager.delete("test_key")
        
        # Both caches should be updated
        mock_memory_cache.delete.assert_called_once_with("default:test_key")
        mock_redis_cache.delete.assert_called_once_with("default:test_key")
    
    @pytest.mark.asyncio
    async def test_query_cache_operations(self, cache_manager):
        """Test query-specific cache operations"""
        query = "test query"
        params = {"limit": 10, "threshold": 0.5}
        result = {"results": ["doc1", "doc2"]}
        
        # Test setting query cache
        await cache_manager.set_query_cache(query, result, params)
        
        # Test getting query cache
        cached_result = await cache_manager.get_query_cache(query, params)
        
        # Should use the same hash for same query+params
        expected_hash = cache_manager._hash_query(query, params)
        assert expected_hash is not None
    
    def test_hash_query_consistency(self, cache_manager):
        """Test that query hashing is consistent"""
        query = "test query"
        params = {"limit": 10, "threshold": 0.5}
        
        hash1 = cache_manager._hash_query(query, params)
        hash2 = cache_manager._hash_query(query, params)
        
        assert hash1 == hash2
        assert len(hash1) == 16  # Should be 16 character hash
    
    def test_hash_query_different_for_different_inputs(self, cache_manager):
        """Test that different queries produce different hashes"""
        hash1 = cache_manager._hash_query("query1", {"limit": 10})
        hash2 = cache_manager._hash_query("query2", {"limit": 10})
        hash3 = cache_manager._hash_query("query1", {"limit": 20})
        
        assert hash1 != hash2
        assert hash1 != hash3
        assert hash2 != hash3
    
    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, cache_manager, mock_memory_cache):
        """Test get_or_set with cache hit"""
        cached_value = {"data": "cached"}
        mock_memory_cache.get.return_value = cached_value
        
        factory_func = MagicMock(return_value={"data": "computed"})
        
        result = await cache_manager.get_or_set(
            "test_key", factory_func
        )
        
        assert result == cached_value
        factory_func.assert_not_called()  # Should not compute if cached
    
    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test get_or_set with cache miss"""
        computed_value = {"data": "computed"}
        mock_memory_cache.get.return_value = None
        mock_redis_cache.get.return_value = None
        
        factory_func = MagicMock(return_value=computed_value)
        
        result = await cache_manager.get_or_set(
            "test_key", factory_func
        )
        
        assert result == computed_value
        factory_func.assert_called_once()
        # Should cache the computed value
        mock_memory_cache.set.assert_called()
        mock_redis_cache.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_or_set_async_factory(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test get_or_set with async factory function"""
        computed_value = {"data": "async_computed"}
        mock_memory_cache.get.return_value = None
        mock_redis_cache.get.return_value = None
        
        async def async_factory():
            return computed_value
        
        result = await cache_manager.get_or_set(
            "test_key", async_factory
        )
        
        assert result == computed_value
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache_manager, mock_redis_cache):
        """Test pattern-based cache invalidation"""
        mock_redis_cache.delete_pattern.return_value = 5
        
        deleted_count = await cache_manager.invalidate_pattern("user:*")
        
        assert deleted_count >= 5  # Should include Redis deletions
        mock_redis_cache.delete_pattern.assert_called_once_with("default:user:*")
    
    @pytest.mark.asyncio
    async def test_get_stats(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test getting comprehensive cache statistics"""
        stats = await cache_manager.get_stats()
        
        assert "manager" in stats
        assert "l1_cache" in stats
        assert "l2_cache" in stats
        
        # Should call get_stats on both caches
        mock_memory_cache.get_stats.assert_called_once()
        mock_redis_cache.get_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test comprehensive health check"""
        health = await cache_manager.health_check()
        
        assert health["status"] == "healthy"
        assert "l1_cache" in health
        assert "l2_cache" in health
        assert "manager_stats" in health
        
        # Should call health_check on both caches
        mock_memory_cache.health_check.assert_called_once()
        mock_redis_cache.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test health check when one component is unhealthy"""
        mock_redis_cache.health_check.return_value = {"status": "unhealthy"}
        
        health = await cache_manager.health_check()
        
        assert health["status"] == "degraded"
    
    def test_make_cache_key(self, cache_manager):
        """Test cache key generation"""
        key = cache_manager._make_cache_key("test_key", "custom_namespace")
        assert key == "custom_namespace:test_key"
        
        key_default = cache_manager._make_cache_key("test_key")
        assert key_default == "default:test_key"
    
    def test_update_hit_ratios(self, cache_manager):
        """Test hit ratio calculation"""
        # Simulate some cache operations
        cache_manager._stats["total_requests"] = 10
        cache_manager._stats["l1_hits"] = 3
        cache_manager._stats["l2_hits"] = 4
        cache_manager._stats["misses"] = 3
        
        cache_manager._update_hit_ratios()
        
        assert cache_manager._stats["l1_hit_ratio"] == 0.3
        assert cache_manager._stats["l2_hit_ratio"] == 0.4
        assert cache_manager._stats["overall_hit_ratio"] == 0.7  # (3+4)/10
    
    @pytest.mark.asyncio
    async def test_close(self, cache_manager, mock_memory_cache, mock_redis_cache):
        """Test closing cache manager"""
        await cache_manager.close()
        
        # Should close both caches
        mock_memory_cache.close.assert_called_once()
        mock_redis_cache.close.assert_called_once()