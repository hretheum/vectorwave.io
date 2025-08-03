"""Edge case tests for Knowledge Base components"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from src.knowledge_engine import CrewAIKnowledgeBase, QueryParams, QuerySource
from src.cache import CacheManager, CacheConfig, MemoryCache, RedisCache
from src.storage import ChromaClient, ChromaDocument, SearchResult


@pytest.mark.edge_case
class TestQueryEdgeCases:
    """Test edge cases in query processing"""
    
    @pytest.fixture
    async def knowledge_base_with_mocks(self):
        """Create knowledge base with all mocked components"""
        cache_config = CacheConfig()
        kb = CrewAIKnowledgeBase(cache_config=cache_config)
        
        # Mock components
        kb.cache_manager = AsyncMock()
        kb.vector_store = AsyncMock()
        kb._health["status"] = "healthy"
        
        return kb
    
    @pytest.mark.asyncio
    async def test_empty_query(self, knowledge_base_with_mocks, edge_case_data):
        """Test handling of empty query string"""
        kb = knowledge_base_with_mocks
        
        # Setup mocks to return empty results
        kb.cache_manager.get_query_cache.return_value = None
        kb.vector_store.search.return_value = []
        
        params = QueryParams(query=edge_case_data["empty_query"])
        
        response = await kb.query(params)
        
        assert response.total_count == 0
        assert len(response.results) == 0
        assert not response.from_cache
        assert kb._stats["total_queries"] == 1
    
    @pytest.mark.asyncio
    async def test_very_long_query(self, knowledge_base_with_mocks, edge_case_data):
        """Test handling of extremely long query strings"""
        kb = knowledge_base_with_mocks
        
        kb.cache_manager.get_query_cache.return_value = None
        kb.vector_store.search.return_value = []
        
        params = QueryParams(query=edge_case_data["very_long_query"])
        
        # Should handle long query without errors
        response = await kb.query(params)
        
        assert response.total_count == 0
        assert kb._stats["total_queries"] == 1
        
        # Verify vector store was called with truncated query or handled gracefully
        kb.vector_store.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_special_characters_query(self, knowledge_base_with_mocks, edge_case_data):
        """Test handling of queries with special characters"""
        kb = knowledge_base_with_mocks
        
        kb.cache_manager.get_query_cache.return_value = None
        kb.vector_store.search.return_value = []
        
        params = QueryParams(query=edge_case_data["special_chars_query"])
        
        response = await kb.query(params)
        
        assert response is not None
        assert kb._stats["total_queries"] == 1
    
    @pytest.mark.asyncio
    async def test_unicode_query(self, knowledge_base_with_mocks, edge_case_data):
        """Test handling of Unicode characters in queries"""
        kb = knowledge_base_with_mocks
        
        kb.cache_manager.get_query_cache.return_value = None
        kb.vector_store.search.return_value = []
        
        params = QueryParams(query=edge_case_data["unicode_query"])
        
        response = await kb.query(params)
        
        assert response is not None
        assert kb._stats["total_queries"] == 1
    
    @pytest.mark.asyncio
    async def test_invalid_score_threshold(self, knowledge_base_with_mocks, edge_case_data):
        """Test handling of invalid score threshold values"""
        kb = knowledge_base_with_mocks
        
        kb.cache_manager.get_query_cache.return_value = None
        kb.vector_store.search.return_value = []
        
        # Test negative threshold
        params = QueryParams(
            query="test query",
            score_threshold=edge_case_data["invalid_score_threshold"]
        )
        
        response = await kb.query(params)
        
        # Should handle gracefully (possibly clamping to valid range)
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_invalid_limit(self, knowledge_base_with_mocks, edge_case_data):
        """Test handling of invalid limit values"""
        kb = knowledge_base_with_mocks
        
        kb.cache_manager.get_query_cache.return_value = None
        kb.vector_store.search.return_value = []
        
        params = QueryParams(
            query="test query",
            limit=edge_case_data["invalid_limit"]
        )
        
        response = await kb.query(params)
        
        # Should handle gracefully (possibly using default limit)
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_null_metadata_filters(self, knowledge_base_with_mocks, edge_case_data):
        """Test handling of null/None metadata filters"""
        kb = knowledge_base_with_mocks
        
        kb.cache_manager.get_query_cache.return_value = None
        kb.vector_store.search.return_value = []
        
        params = QueryParams(
            query="test query",
            metadata_filters=edge_case_data["null_metadata"]
        )
        
        response = await kb.query(params)
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_large_metadata_filters(self, knowledge_base_with_mocks, edge_case_data):
        """Test handling of very large metadata filter objects"""
        kb = knowledge_base_with_mocks
        
        kb.cache_manager.get_query_cache.return_value = None
        kb.vector_store.search.return_value = []
        
        params = QueryParams(
            query="test query",
            metadata_filters=edge_case_data["large_metadata"]
        )
        
        response = await kb.query(params)
        
        assert response is not None
        
        # Verify the large metadata was passed to vector store
        call_args = kb.vector_store.search.call_args
        assert call_args[1]["where"] == edge_case_data["large_metadata"]
    
    @pytest.mark.asyncio
    async def test_concurrent_identical_queries(self, knowledge_base_with_mocks):
        """Test race conditions with identical concurrent queries"""
        kb = knowledge_base_with_mocks
        
        # Setup cache to simulate race condition
        call_count = 0
        
        async def mock_cache_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call - cache miss, but slow to respond
                await asyncio.sleep(0.1)
                return None
            else:
                # Subsequent calls - also miss (race condition)
                return None
        
        kb.cache_manager.get_query_cache.side_effect = mock_cache_get
        kb.vector_store.search.return_value = [
            SearchResult(
                document=ChromaDocument(
                    id="race_doc",
                    content="Race condition test",
                    metadata={"title": "Race Test"}
                ),
                score=0.9,
                distance=0.1
            )
        ]
        
        # Execute 5 identical queries concurrently
        params = QueryParams(query="race condition test")
        tasks = [kb.query(params) for _ in range(5)]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(responses) == 5
        assert all(len(r.results) > 0 for r in responses)
        
        # Should handle race conditions gracefully
        assert kb._stats["total_queries"] == 5
    
    @pytest.mark.asyncio
    async def test_component_failure_recovery(self, knowledge_base_with_mocks):
        """Test recovery when components fail temporarily"""
        kb = knowledge_base_with_mocks
        
        # Setup cache to fail then recover
        call_count = 0
        
        async def mock_cache_with_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary cache failure")
            else:
                return None  # Cache miss after recovery
        
        kb.cache_manager.get_query_cache.side_effect = mock_cache_with_failure
        kb.vector_store.search.return_value = []
        
        params = QueryParams(query="failure recovery test")
        
        # First two queries should handle cache failure gracefully
        response1 = await kb.query(params)
        response2 = await kb.query(params)
        
        # Third query should work normally (cache recovered)
        response3 = await kb.query(params)
        
        # All should complete without raising exceptions
        assert response1 is not None
        assert response2 is not None
        assert response3 is not None
        assert kb._stats["total_queries"] == 3


@pytest.mark.edge_case
class TestCacheEdgeCases:
    """Test edge cases in cache operations"""
    
    @pytest.mark.asyncio
    async def test_memory_cache_overflow(self):
        """Test memory cache behavior when it exceeds size limits"""
        # Create cache with very small size
        cache = MemoryCache(max_size_mb=1, default_ttl_seconds=300)
        
        # Add many large entries to trigger overflow
        large_value = "x" * (1024 * 100)  # 100KB
        
        for i in range(20):  # Add 2MB of data to 1MB cache
            await cache.set(f"key_{i}", large_value)
        
        # Should have triggered evictions
        stats = await cache.get_stats()
        assert stats["evictions"] > 0
        assert stats["entries_count"] < 20
        
        # Cache should still be functional
        await cache.set("test_key", "test_value")
        result = await cache.get("test_key")
        assert result == "test_value"
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_ttl_edge_cases(self):
        """Test TTL edge cases"""
        cache = MemoryCache(default_ttl_seconds=1)
        
        # Test with very short TTL
        await cache.set("short_ttl", "value", ttl_seconds=0.1)
        
        # Should be available immediately
        result = await cache.get("short_ttl")
        assert result == "value"
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Should be expired
        result = await cache.get("short_ttl")
        assert result is None
        
        # Test with zero TTL (should expire immediately)
        await cache.set("zero_ttl", "value", ttl_seconds=0)
        result = await cache.get("zero_ttl")
        assert result is None  # Should be expired immediately
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_redis_cache_serialization_edge_cases(self):
        """Test Redis cache with difficult-to-serialize objects"""
        cache = RedisCache()
        cache._redis = AsyncMock()
        
        # Test with complex nested objects
        complex_object = {
            "nested": {
                "list": [1, 2, {"inner": "value"}],
                "tuple": (1, 2, 3),  # Will be converted to list
                "none_value": None,
                "bool_value": True,
                "float_value": 3.14159
            }
        }
        
        # Should handle complex serialization
        cache._redis.setex.return_value = True
        success = await cache.set("complex", complex_object)
        assert success is True
        
        # Verify JSON serialization was called
        call_args = cache._redis.setex.call_args
        serialized_data = call_args[0][2]
        
        # Should be valid JSON
        parsed = json.loads(serialized_data)
        assert parsed["nested"]["list"] == [1, 2, {"inner": "value"}]
        assert parsed["nested"]["none_value"] is None
    
    @pytest.mark.asyncio
    async def test_cache_key_collision_handling(self):
        """Test handling of cache key collisions and special characters"""
        cache_config = CacheConfig(memory_enabled=True, redis_enabled=False)
        memory_cache = MemoryCache()
        cache_manager = CacheManager(cache_config)
        await cache_manager.initialize(memory_cache, None)
        
        # Test keys with special characters that could cause collisions
        special_keys = [
            "key:with:colons",
            "key with spaces",
            "key/with/slashes",
            "key\\with\\backslashes",
            "key.with.dots",
            "key-with-dashes",
            "key_with_underscores",
            "key#with#hashes",
            "ключ-с-кириллицей",  # Cyrillic
            "キー", # Japanese
            "🔑", # Emoji
        ]
        
        # Set values for all special keys
        for i, key in enumerate(special_keys):
            await cache_manager.set(key, f"value_{i}")
        
        # Retrieve all values
        for i, key in enumerate(special_keys):
            result = await cache_manager.get(key)
            assert result == f"value_{i}", f"Failed for key: {key}"
        
        await cache_manager.close()


@pytest.mark.edge_case
class TestVectorStoreEdgeCases:
    """Test edge cases in vector store operations"""
    
    @pytest.mark.asyncio
    async def test_chroma_client_with_malformed_responses(self):
        """Test ChromaClient handling of malformed responses"""
        client = ChromaClient()
        client._collection = MagicMock()
        
        # Test with malformed query response
        malformed_responses = [
            # Missing required fields
            {"documents": [[]], "metadatas": [[]]},  # Missing distances, ids
            
            # Mismatched array lengths
            {
                "documents": [["doc1", "doc2"]],
                "metadatas": [[{"title": "title1"}]],  # Only one metadata
                "distances": [[0.1, 0.2]],
                "ids": [["id1", "id2"]]
            },
            
            # None values
            {
                "documents": [["doc1", None]],
                "metadatas": [[{"title": "title1"}, None]],
                "distances": [[0.1, None]],
                "ids": [["id1", None]]
            },
            
            # Empty nested arrays
            {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
                "ids": [[]]
            }
        ]
        
        for malformed_response in malformed_responses:
            client._collection.query.return_value = malformed_response
            
            # Should handle malformed responses gracefully
            try:
                results = await client.search("test query")
                # Should return empty list or handle gracefully
                assert isinstance(results, list)
            except Exception as e:
                # If it raises an exception, it should be handled gracefully
                # in the knowledge engine layer
                assert "malformed" in str(e).lower() or "missing" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_document_with_extreme_values(self):
        """Test document handling with extreme values"""
        client = ChromaClient()
        client._collection = MagicMock()
        
        # Test documents with extreme characteristics
        extreme_documents = [
            # Very large document
            ChromaDocument(
                id="large_doc",
                content="x" * (1024 * 1024),  # 1MB content
                metadata={"size": "large"}
            ),
            
            # Document with many metadata fields
            ChromaDocument(
                id="metadata_heavy_doc",
                content="Small content",
                metadata={f"field_{i}": f"value_{i}" for i in range(1000)}
            ),
            
            # Document with Unicode content
            ChromaDocument(
                id="unicode_doc",
                content="Unicode content: 🚀 人工智能 مرحبا Здравствуй",
                metadata={"language": "mixed"}
            ),
            
            # Document with special characters
            ChromaDocument(
                id="special_chars_doc",
                content="Special chars: !@#$%^&*()_+-={}|[]\\:\";'<>?,./",
                metadata={"type": "special"}
            )
        ]
        
        # Should handle all extreme documents without errors
        for doc in extreme_documents:
            await client.add_documents([doc])
            client._collection.add.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_with_extreme_parameters(self):
        """Test search with extreme parameter values"""
        client = ChromaClient()
        client._collection = MagicMock()
        client._collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        
        extreme_params = [
            # Very high limit
            {"query": "test", "limit": 100000},
            
            # Zero limit
            {"query": "test", "limit": 0},
            
            # Extreme thresholds
            {"query": "test", "score_threshold": 1.1},  # Above 1.0
            {"query": "test", "score_threshold": -0.5},  # Below 0.0
            
            # Complex metadata filters
            {
                "query": "test",
                "where": {
                    "$and": [
                        {"field1": {"$eq": "value1"}},
                        {"field2": {"$ne": "value2"}},
                        {"field3": {"$in": ["val1", "val2", "val3"]}},
                        {"field4": {"$nin": ["val4", "val5"]}},
                        {"field5": {"$gt": 100}},
                        {"field6": {"$gte": 50}},
                        {"field7": {"$lt": 200}},
                        {"field8": {"$lte": 150}}
                    ]
                }
            }
        ]
        
        for params in extreme_params:
            # Should handle extreme parameters gracefully
            results = await client.search(**params)
            assert isinstance(results, list)


@pytest.mark.edge_case
class TestErrorHandlingEdgeCases:
    """Test comprehensive error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_network_timeout_scenarios(self, error_simulator):
        """Test handling of network timeouts"""
        cache = RedisCache()
        mock_redis = AsyncMock()
        
        # Simulate various timeout scenarios
        timeout_scenarios = [
            ("get", error_simulator.timeout_error()),
            ("setex", error_simulator.timeout_error()),
            ("delete", error_simulator.timeout_error()),
            ("ping", error_simulator.timeout_error())
        ]
        
        for method, error in timeout_scenarios:
            # Reset mock
            mock_redis.reset_mock()
            setattr(mock_redis, method, AsyncMock(side_effect=error))
            cache._redis = mock_redis
            
            # Operations should handle timeouts gracefully
            if method == "get":
                result = await cache.get("test_key")
                assert result is None
                assert cache._stats["errors"] > 0
            
            elif method == "setex":
                success = await cache.set("test_key", "test_value")
                assert success is False
                assert cache._stats["errors"] > 0
            
            elif method == "delete":
                success = await cache.delete("test_key")
                assert success is False
                assert cache._stats["errors"] > 0
            
            elif method == "ping":
                health = await cache.health_check()
                assert health["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_memory_exhaustion_scenarios(self, error_simulator):
        """Test handling of memory exhaustion"""
        cache = MemoryCache(max_size_mb=1)  # Very small cache
        
        # Try to add data that would cause memory issues
        with patch('src.cache.memory_cache.CacheEntry', side_effect=error_simulator.memory_error()):
            # Should handle memory errors gracefully
            try:
                await cache.set("memory_test", "large_value" * 1000)
            except MemoryError:
                # If it raises MemoryError, that's acceptable
                pass
            
            # Cache should still be functional for smaller operations
            await cache.set("small_key", "small_value")
            result = await cache.get("small_key")
            # Either succeeds or fails gracefully
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_serialization_error_scenarios(self, error_simulator):
        """Test handling of serialization errors"""
        cache = RedisCache()
        cache._redis = AsyncMock()
        cache._redis.setex.return_value = True
        
        # Objects that can't be JSON serialized
        unserializable_objects = [
            lambda x: x,  # Function
            type,  # Type object
            open,  # Built-in function
            {"circular": None}  # Will create circular reference
        ]
        
        # Create circular reference
        circular = {"ref": None}
        circular["ref"] = circular
        unserializable_objects[-1] = circular
        
        for obj in unserializable_objects:
            success = await cache.set("unserializable", obj)
            assert success is False  # Should fail gracefully
            
            # Redis should not be called for unserializable objects
            cache._redis.setex.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_concurrent_access_edge_cases(self):
        """Test edge cases in concurrent access"""
        cache = MemoryCache(max_size_mb=5)
        
        async def aggressive_cache_operations(worker_id):
            """Perform aggressive cache operations"""
            operations = []
            for i in range(100):
                key = f"worker_{worker_id}_key_{i}"
                
                # Mix of operations
                await cache.set(key, f"value_{i}")
                operations.append(("set", key))
                
                if i % 3 == 0:
                    await cache.delete(key)
                    operations.append(("delete", key))
                
                if i % 5 == 0:
                    await cache.get(key)
                    operations.append(("get", key))
                
                if i % 10 == 0:
                    await cache.clear()
                    operations.append(("clear", None))
            
            return operations
        
        # Run 10 workers concurrently
        tasks = [aggressive_cache_operations(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle concurrent operations without deadlocks or crashes
        assert len(results) == 10
        
        # None of the results should be exceptions
        for result in results:
            assert not isinstance(result, Exception)
        
        # Cache should still be functional
        await cache.set("final_test", "final_value")
        result = await cache.get("final_test")
        assert result == "final_value"
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_edge_cases(self):
        """Test resource cleanup in edge cases"""
        cache = MemoryCache()
        
        # Simulate abnormal shutdown scenarios
        try:
            # Start some background operations
            await cache.set("test1", "value1")
            await cache.set("test2", "value2")
            
            # Simulate task cancellation during operation
            async def interrupted_operation():
                await cache.set("interrupted", "value")
                await asyncio.sleep(1)  # Simulate long operation
                await cache.get("interrupted")
            
            task = asyncio.create_task(interrupted_operation())
            await asyncio.sleep(0.1)  # Let it start
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass  # Expected
            
            # Cache should still be functional after interruption
            await cache.set("after_cancel", "value")
            result = await cache.get("after_cancel")
            assert result == "value"
            
        finally:
            # Should clean up gracefully even after interruptions
            await cache.close()


@pytest.mark.edge_case
@pytest.mark.performance
class TestPerformanceEdgeCases:
    """Test performance edge cases and limits"""
    
    @pytest.mark.asyncio
    async def test_high_frequency_operations(self):
        """Test system behavior under very high operation frequency"""
        cache = MemoryCache(max_size_mb=10)
        
        # Perform operations as fast as possible
        start_time = asyncio.get_event_loop().time()
        
        operations = 0
        duration = 1.0  # 1 second test
        
        while (asyncio.get_event_loop().time() - start_time) < duration:
            await cache.set(f"freq_key_{operations}", f"value_{operations}")
            await cache.get(f"freq_key_{operations}")
            operations += 1
        
        end_time = asyncio.get_event_loop().time()
        actual_duration = end_time - start_time
        ops_per_second = operations / actual_duration
        
        # Should handle high frequency operations
        assert ops_per_second > 100  # At least 100 ops/second
        assert operations > 100  # Should complete many operations
        
        # Cache should still be responsive
        await cache.set("responsive_test", "test")
        result = await cache.get("responsive_test")
        assert result == "test"
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_memory_pressure_behavior(self):
        """Test behavior under memory pressure"""
        # Create cache with limited memory
        cache = MemoryCache(max_size_mb=2, default_ttl_seconds=300)
        
        # Fill cache to capacity and beyond
        large_value = "x" * (1024 * 50)  # 50KB values
        
        successful_sets = 0
        for i in range(100):  # Try to add 5MB to 2MB cache
            try:
                await cache.set(f"pressure_key_{i}", large_value)
                successful_sets += 1
            except Exception:
                # Some sets might fail under pressure
                pass
        
        # Should have triggered evictions
        stats = await cache.get_stats()
        assert stats["evictions"] > 0
        
        # Cache should still be functional
        await cache.set("functionality_test", "small_value")
        result = await cache.get("functionality_test")
        assert result == "small_value"
        
        # Should maintain reasonable number of entries
        assert stats["entries_count"] < 100
        assert stats["entries_count"] > 0
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_query_complexity_limits(self, knowledge_base_with_mocks):
        """Test handling of extremely complex queries"""
        kb = knowledge_base_with_mocks
        
        # Setup mocks
        kb.cache_manager.get_query_cache.return_value = None
        kb.vector_store.search.return_value = []
        
        # Create extremely complex query parameters
        complex_metadata_filter = {}
        
        # Build nested complex filter
        for i in range(100):  # Very deep nesting
            if i == 0:
                complex_metadata_filter["level_0"] = {"$eq": f"value_{i}"}
            else:
                complex_metadata_filter[f"level_{i}"] = {
                    "$and": [
                        {"field_a": {"$in": [f"val_{j}" for j in range(10)]}},
                        {"field_b": {"$gte": i}},
                        {"field_c": {"$ne": f"exclude_{i}"}},
                        {"$or": [
                            {"nested_1": {"$lt": i * 10}},
                            {"nested_2": {"$regex": f"pattern_{i}"}}
                        ]}
                    ]
                }
        
        params = QueryParams(
            query="x" * 10000,  # Very long query
            limit=10000,  # Very high limit
            metadata_filters=complex_metadata_filter
        )
        
        # Should handle complex query without crashing
        response = await kb.query(params)
        
        assert response is not None
        assert kb._stats["total_queries"] == 1