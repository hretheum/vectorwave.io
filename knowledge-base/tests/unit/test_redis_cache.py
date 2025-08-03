"""Unit tests for RedisCache"""

import pytest
import json
import time
from unittest.mock import AsyncMock, patch, MagicMock
from src.cache.redis_cache import RedisCache


@pytest.mark.unit
class TestRedisCache:
    """Test RedisCache functionality"""
    
    @pytest.fixture
    def redis_cache(self):
        """Create RedisCache instance for testing"""
        return RedisCache(
            redis_url="redis://localhost:6379",
            db=1,
            max_connections=10,
            default_ttl_seconds=3600,
            key_prefix="test_kb"
        )
    
    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client"""
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = "PONG"
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.keys.return_value = []
        mock_redis.exists.return_value = 0
        mock_redis.ttl.return_value = -2
        mock_redis.info.return_value = {
            "used_memory": 1024 * 1024,  # 1MB
            "redis_version": "6.0.0"
        }
        mock_redis.close.return_value = None
        return mock_redis
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, redis_cache, mock_redis_client):
        """Test successful Redis initialization"""
        with patch('aioredis.from_url', return_value=mock_redis_client):
            await redis_cache.initialize()
            
            assert redis_cache._redis == mock_redis_client
            mock_redis_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, redis_cache):
        """Test Redis initialization failure"""
        with patch('aioredis.from_url', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await redis_cache.initialize()
    
    def test_make_key(self, redis_cache):
        """Test key prefixing"""
        key = redis_cache._make_key("test_key")
        assert key == "test_kb:test_key"
    
    @pytest.mark.asyncio
    async def test_set_and_get_success(self, redis_cache, mock_redis_client):
        """Test successful set and get operations"""
        redis_cache._redis = mock_redis_client
        
        test_data = {"key": "value", "number": 42}
        serialized_data = json.dumps(test_data, default=str)
        mock_redis_client.get.return_value = serialized_data
        
        # Test set
        success = await redis_cache.set("test_key", test_data)
        assert success is True
        
        mock_redis_client.setex.assert_called_once_with(
            "test_kb:test_key", 3600, serialized_data
        )
        
        # Test get
        result = await redis_cache.get("test_key")
        assert result == test_data
        
        mock_redis_client.get.assert_called_once_with("test_kb:test_key")
        assert redis_cache._stats["hits"] == 1
        assert redis_cache._stats["sets"] == 1
    
    @pytest.mark.asyncio
    async def test_get_miss(self, redis_cache, mock_redis_client):
        """Test cache miss"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.get.return_value = None
        
        result = await redis_cache.get("nonexistent_key")
        
        assert result is None
        assert redis_cache._stats["misses"] == 1
        assert redis_cache._stats["hit_ratio"] == 0.0
    
    @pytest.mark.asyncio
    async def test_get_corrupted_data(self, redis_cache, mock_redis_client):
        """Test handling of corrupted JSON data"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.get.return_value = "invalid json"
        
        result = await redis_cache.get("corrupted_key")
        
        assert result is None
        assert redis_cache._stats["misses"] == 1
        # Should attempt to delete corrupted entry
        mock_redis_client.delete.assert_called_once_with("test_kb:corrupted_key")
    
    @pytest.mark.asyncio
    async def test_set_serialization_error(self, redis_cache, mock_redis_client):
        """Test handling of serialization errors"""
        redis_cache._redis = mock_redis_client
        
        # Object that can't be serialized
        unserializable_obj = {"set": set([1, 2, 3])}  # sets can't be JSON serialized
        
        success = await redis_cache.set("bad_key", unserializable_obj)
        
        assert success is False
        mock_redis_client.setex.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_success(self, redis_cache, mock_redis_client):
        """Test successful delete operation"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.delete.return_value = 1
        
        success = await redis_cache.delete("test_key")
        
        assert success is True
        mock_redis_client.delete.assert_called_once_with("test_kb:test_key")
        assert redis_cache._stats["deletes"] == 1
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, redis_cache, mock_redis_client):
        """Test deleting nonexistent key"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.delete.return_value = 0
        
        success = await redis_cache.delete("nonexistent_key")
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_delete_pattern(self, redis_cache, mock_redis_client):
        """Test pattern-based deletion"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.keys.return_value = ["test_kb:key1", "test_kb:key2"]
        mock_redis_client.delete.return_value = 2
        
        deleted_count = await redis_cache.delete_pattern("key*")
        
        assert deleted_count == 2
        mock_redis_client.keys.assert_called_once_with("test_kb:key*")
        mock_redis_client.delete.assert_called_once_with("test_kb:key1", "test_kb:key2")
        assert redis_cache._stats["deletes"] == 2
    
    @pytest.mark.asyncio
    async def test_delete_pattern_no_keys(self, redis_cache, mock_redis_client):
        """Test pattern deletion with no matching keys"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.keys.return_value = []
        
        deleted_count = await redis_cache.delete_pattern("nomatch*")
        
        assert deleted_count == 0
        mock_redis_client.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, redis_cache, mock_redis_client):
        """Test clearing entire cache"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.keys.return_value = ["test_kb:key1", "test_kb:key2"]
        mock_redis_client.delete.return_value = 2
        
        success = await redis_cache.clear()
        
        assert success is True
        mock_redis_client.keys.assert_called_once_with("test_kb:*")
        mock_redis_client.delete.assert_called_once_with("test_kb:key1", "test_kb:key2")
    
    @pytest.mark.asyncio
    async def test_clear_empty_cache(self, redis_cache, mock_redis_client):
        """Test clearing empty cache"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.keys.return_value = []
        
        success = await redis_cache.clear()
        
        assert success is True
        mock_redis_client.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_exists(self, redis_cache, mock_redis_client):
        """Test key existence check"""
        redis_cache._redis = mock_redis_client
        
        # Key exists
        mock_redis_client.exists.return_value = 1
        exists = await redis_cache.exists("existing_key")
        assert exists is True
        
        # Key doesn't exist
        mock_redis_client.exists.return_value = 0
        exists = await redis_cache.exists("nonexistent_key")
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_ttl(self, redis_cache, mock_redis_client):
        """Test TTL operations"""
        redis_cache._redis = mock_redis_client
        
        # Key with TTL
        mock_redis_client.ttl.return_value = 300
        ttl = await redis_cache.ttl("key_with_ttl")
        assert ttl == 300
        
        # Key without TTL
        mock_redis_client.ttl.return_value = -1
        ttl = await redis_cache.ttl("persistent_key")
        assert ttl == -1
        
        # Nonexistent key
        mock_redis_client.ttl.return_value = -2
        ttl = await redis_cache.ttl("nonexistent_key")
        assert ttl == -2
    
    @pytest.mark.asyncio
    async def test_keys(self, redis_cache, mock_redis_client):
        """Test getting keys with pattern"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.keys.return_value = [
            "test_kb:user:1",
            "test_kb:user:2",
            "test_kb:session:123"
        ]
        
        keys = await redis_cache.keys("user:*")
        
        # Should return keys without prefix
        assert "user:1" in keys
        assert "user:2" in keys
        assert "session:123" not in keys  # Doesn't match pattern
        
        mock_redis_client.keys.assert_called_once_with("test_kb:user:*")
    
    @pytest.mark.asyncio
    async def test_get_stats_connected(self, redis_cache, mock_redis_client):
        """Test getting statistics when connected"""
        redis_cache._redis = mock_redis_client
        redis_cache._stats["hits"] = 10
        redis_cache._stats["misses"] = 2
        
        mock_redis_client.keys.return_value = ["test_kb:key1", "test_kb:key2"]
        
        stats = await redis_cache.get_stats()
        
        assert stats["status"] == "connected"
        assert stats["hits"] == 10
        assert stats["misses"] == 2
        assert stats["used_memory_mb"] == 1.0  # 1MB from mock
        assert stats["our_keys_count"] == 2
        assert stats["redis_version"] == "6.0.0"
    
    @pytest.mark.asyncio
    async def test_get_stats_disconnected(self, redis_cache):
        """Test getting statistics when disconnected"""
        redis_cache._redis = None
        
        stats = await redis_cache.get_stats()
        
        assert stats["status"] == "disconnected"
        assert "hits" in stats
        assert "misses" in stats
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, redis_cache, mock_redis_client):
        """Test successful health check"""
        redis_cache._redis = mock_redis_client
        
        # Mock successful operations
        test_value = {"timestamp": time.time(), "status": "ok"}
        mock_redis_client.get.return_value = json.dumps(test_value, default=str)
        
        health = await redis_cache.health_check()
        
        assert health["status"] == "healthy"
        assert health["operations"] == "ok"
        assert "stats" in health
        
        # Should perform ping and basic operations
        mock_redis_client.ping.assert_called()
        mock_redis_client.setex.assert_called()
        mock_redis_client.get.assert_called()
        mock_redis_client.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, redis_cache):
        """Test health check when not initialized"""
        redis_cache._redis = None
        
        health = await redis_cache.health_check()
        
        assert health["status"] == "unhealthy"
        assert "Redis client not initialized" in health["error"]
    
    @pytest.mark.asyncio
    async def test_health_check_ping_failure(self, redis_cache, mock_redis_client):
        """Test health check with ping failure"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.ping.side_effect = Exception("Connection lost")
        
        health = await redis_cache.health_check()
        
        assert health["status"] == "unhealthy"
        assert "Connection lost" in health["error"]
    
    @pytest.mark.asyncio
    async def test_error_handling_get(self, redis_cache, mock_redis_client):
        """Test error handling in get operation"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.get.side_effect = Exception("Redis error")
        
        result = await redis_cache.get("test_key")
        
        assert result is None
        assert redis_cache._stats["errors"] == 1
        assert redis_cache._stats["misses"] == 1
    
    @pytest.mark.asyncio
    async def test_error_handling_set(self, redis_cache, mock_redis_client):
        """Test error handling in set operation"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.setex.side_effect = Exception("Redis error")
        
        success = await redis_cache.set("test_key", "test_value")
        
        assert success is False
        assert redis_cache._stats["errors"] == 1
    
    @pytest.mark.asyncio
    async def test_error_handling_delete(self, redis_cache, mock_redis_client):
        """Test error handling in delete operation"""
        redis_cache._redis = mock_redis_client
        mock_redis_client.delete.side_effect = Exception("Redis error")
        
        success = await redis_cache.delete("test_key")
        
        assert success is False
        assert redis_cache._stats["errors"] == 1
    
    @pytest.mark.asyncio
    async def test_hit_ratio_calculation(self, redis_cache, mock_redis_client):
        """Test hit ratio calculation"""
        redis_cache._redis = mock_redis_client
        
        # Simulate hits and misses
        redis_cache._stats["hits"] = 7
        redis_cache._stats["misses"] = 3
        redis_cache._update_hit_ratio()
        
        assert redis_cache._stats["hit_ratio"] == 0.7
        
        # Test with no requests
        redis_cache._stats["hits"] = 0
        redis_cache._stats["misses"] = 0
        redis_cache._update_hit_ratio()
        
        assert redis_cache._stats["hit_ratio"] == 0.0
    
    @pytest.mark.asyncio
    async def test_close(self, redis_cache, mock_redis_client):
        """Test closing Redis connection"""
        redis_cache._redis = mock_redis_client
        
        await redis_cache.close()
        
        mock_redis_client.close.assert_called_once()
        assert redis_cache._redis is None
    
    @pytest.mark.asyncio
    async def test_operations_without_initialization(self, redis_cache):
        """Test that operations fail gracefully without initialization"""
        # All operations should raise RuntimeError
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            await redis_cache.get("key")
        
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            await redis_cache.set("key", "value")
        
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            await redis_cache.delete("key")
        
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            await redis_cache.clear()
    
    @pytest.mark.asyncio
    async def test_custom_ttl(self, redis_cache, mock_redis_client):
        """Test setting custom TTL"""
        redis_cache._redis = mock_redis_client
        custom_ttl = 1800
        
        await redis_cache.set("test_key", "test_value", ttl_seconds=custom_ttl)
        
        mock_redis_client.setex.assert_called_once_with(
            "test_kb:test_key", custom_ttl, '"test_value"'
        )


@pytest.mark.unit
@pytest.mark.performance
class TestRedisCachePerformance:
    """Performance tests for RedisCache"""
    
    @pytest.mark.asyncio
    async def test_serialization_performance(self):
        """Test JSON serialization/deserialization performance"""
        cache = RedisCache()
        
        # Large object for serialization test
        large_obj = {
            "data": ["item_" + str(i) for i in range(1000)],
            "metadata": {"key_" + str(i): f"value_{i}" for i in range(100)},
            "nested": {
                "level1": {
                    "level2": {
                        "items": list(range(500))
                    }
                }
            }
        }
        
        start_time = time.time()
        
        # Serialize multiple times
        for _ in range(100):
            serialized = json.dumps(large_obj, default=str)
            deserialized = json.loads(serialized)
            assert deserialized["data"][0] == "item_0"
        
        end_time = time.time()
        
        # Should complete serialization operations quickly
        assert (end_time - start_time) < 1.0  # 1 second for 100 operations
    
    @pytest.mark.asyncio
    async def test_key_pattern_performance(self):
        """Test performance of key pattern operations"""
        cache = RedisCache(key_prefix="perf_test")
        
        # Test key generation performance
        start_time = time.time()
        
        keys = []
        for i in range(10000):
            key = cache._make_key(f"performance_key_{i}")
            keys.append(key)
        
        end_time = time.time()
        
        # Should generate keys quickly
        assert (end_time - start_time) < 0.1  # 100ms for 10k keys
        assert len(keys) == 10000
        assert all(key.startswith("perf_test:") for key in keys)