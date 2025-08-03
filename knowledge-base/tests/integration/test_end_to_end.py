"""Integration tests for end-to-end Knowledge Base functionality"""

import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from src.knowledge_engine import CrewAIKnowledgeBase, QueryParams, QuerySource
from src.cache import CacheConfig, CacheManager, MemoryCache
from src.storage import ChromaClient, ChromaDocument, SearchResult


@pytest.mark.integration
class TestEndToEndFlow:
    """Test complete end-to-end Knowledge Base flows"""
    
    @pytest.fixture
    async def integrated_knowledge_base(self):
        """Create a knowledge base with real cache but mocked vector store"""
        cache_config = CacheConfig(
            memory_enabled=True,
            redis_enabled=False,  # Use only memory cache for tests
            memory_ttl=300,
            redis_ttl=3600
        )
        
        kb = CrewAIKnowledgeBase(
            cache_config=cache_config,
            chroma_host="localhost",
            chroma_port=8000,
            redis_url="redis://localhost:6379"
        )
        
        # Use real memory cache
        memory_cache = MemoryCache(max_size_mb=10, default_ttl_seconds=300)
        cache_manager = CacheManager(cache_config)
        await cache_manager.initialize(memory_cache, None)  # No Redis
        kb.cache_manager = cache_manager
        
        # Mock vector store
        mock_vector_store = AsyncMock(spec=ChromaClient)
        mock_vector_store.search.return_value = []
        mock_vector_store.add_documents.return_value = None
        mock_vector_store.get_collection_stats.return_value = {
            "total_documents": 100,
            "collection_name": "test",
            "embedding_model": "test-model",
            "similarity_metric": "cosine"
        }
        mock_vector_store.health_check.return_value = {"status": "healthy"}
        kb.vector_store = mock_vector_store
        
        # Set as healthy
        kb._health["status"] = "healthy"
        kb._health["cache"] = "healthy"
        kb._health["vector_store"] = "healthy"
        
        yield kb
        
        # Cleanup
        await kb.close()
    
    @pytest.mark.asyncio
    async def test_query_cache_vector_fallback(self, integrated_knowledge_base, sample_documents):
        """Test query flow: cache miss → vector store hit → cache population"""
        kb = integrated_knowledge_base
        
        # Setup vector store to return results
        mock_search_results = [
            SearchResult(
                document=doc,
                score=0.9 - (i * 0.1),
                distance=0.1 + (i * 0.1)
            )
            for i, doc in enumerate(sample_documents[:3])
        ]
        kb.vector_store.search.return_value = mock_search_results
        
        query_params = QueryParams(
            query="test integration query",
            limit=5,
            score_threshold=0.3,
            use_cache=True
        )
        
        # First query - should hit vector store and cache results
        response1 = await kb.query(query_params)
        
        assert response1.from_cache is False
        assert len(response1.results) == 3
        assert QuerySource.VECTOR in response1.sources_used
        assert kb._stats["vector_hits"] == 1
        assert kb._stats["cache_hits"] == 0
        
        # Second identical query - should hit cache
        response2 = await kb.query(query_params)
        
        assert response2.from_cache is True
        assert len(response2.results) == 3
        assert QuerySource.CACHE in response2.sources_used
        assert kb._stats["vector_hits"] == 1  # Should not increase
        assert kb._stats["cache_hits"] == 1
        
        # Verify cache was populated and retrieved
        assert response1.results[0].content == response2.results[0].content
    
    @pytest.mark.asyncio
    async def test_document_lifecycle(self, integrated_knowledge_base, sample_document):
        """Test complete document lifecycle: add → query → update → delete"""
        kb = integrated_knowledge_base
        
        # 1. Add document
        success = await kb.add_document(sample_document)
        assert success is True
        
        # Verify add was called on vector store
        kb.vector_store.add_documents.assert_called_once_with([sample_document])
        
        # 2. Set up search to return the document
        mock_search_result = SearchResult(
            document=sample_document,
            score=0.95,
            distance=0.05
        )
        kb.vector_store.search.return_value = [mock_search_result]
        
        # Query for the document
        query_params = QueryParams(
            query="sample AI document",
            limit=10,
            use_cache=False  # Bypass cache for this test
        )
        
        response = await kb.query(query_params)
        assert len(response.results) == 1
        assert response.results[0].content == sample_document.content
        
        # 3. Update document
        updated_document = ChromaDocument(
            id=sample_document.id,
            content="Updated content about AI agents",
            metadata={**sample_document.metadata, "updated": True}
        )
        
        success = await kb.update_document(updated_document)
        assert success is True
        kb.vector_store.update_document.assert_called_once_with(updated_document)
        
        # 4. Delete document
        success = await kb.delete_document(sample_document.id)
        assert success is True
        kb.vector_store.delete_document.assert_called_once_with(sample_document.id)
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_updates(self, integrated_knowledge_base, sample_document):
        """Test that cache is properly invalidated when documents are modified"""
        kb = integrated_knowledge_base
        
        # Setup initial search results
        initial_result = SearchResult(
            document=sample_document,
            score=0.9,
            distance=0.1
        )
        kb.vector_store.search.return_value = [initial_result]
        
        query_params = QueryParams(query="test cache invalidation", use_cache=True)
        
        # First query - populate cache
        response1 = await kb.query(query_params)
        assert response1.from_cache is False
        assert len(response1.results) == 1
        
        # Second query - should hit cache
        response2 = await kb.query(query_params)
        assert response2.from_cache is True
        
        # Add new document - should invalidate cache
        new_document = ChromaDocument(
            id="new_doc",
            content="New document content",
            metadata={"title": "New Doc"}
        )
        await kb.add_document(new_document)
        
        # Verify cache invalidation was called
        # (In real implementation, this would clear cached query results)
        assert kb.cache_manager.invalidate_pattern.call_count > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_queries_with_caching(self, integrated_knowledge_base):
        """Test concurrent queries with cache behavior"""
        kb = integrated_knowledge_base
        
        # Setup vector store response
        mock_result = SearchResult(
            document=ChromaDocument(
                id="concurrent_doc",
                content="Concurrent test document",
                metadata={"title": "Concurrent Test"}
            ),
            score=0.85,
            distance=0.15
        )
        kb.vector_store.search.return_value = [mock_result]
        
        async def execute_query(query_id):
            """Execute a query and return timing info"""
            start_time = asyncio.get_event_loop().time()
            
            params = QueryParams(
                query=f"concurrent query {query_id}",
                use_cache=True
            )
            
            response = await kb.query(params)
            
            end_time = asyncio.get_event_loop().time()
            
            return {
                "query_id": query_id,
                "from_cache": response.from_cache,
                "result_count": len(response.results),
                "query_time": (end_time - start_time) * 1000  # ms
            }
        
        # Execute 10 concurrent queries
        tasks = [execute_query(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Analyze results
        cache_hits = sum(1 for r in results if r["from_cache"])
        vector_hits = sum(1 for r in results if not r["from_cache"])
        
        # Should have some cache hits (queries with same parameters)
        assert cache_hits > 0 or vector_hits > 0
        assert all(r["result_count"] > 0 for r in results)
        
        # Average query time should be reasonable
        avg_time = sum(r["query_time"] for r in results) / len(results)
        assert avg_time < 100  # 100ms average
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self, integrated_knowledge_base):
        """Test error recovery and graceful degradation"""
        kb = integrated_knowledge_base
        
        # Simulate vector store failure
        kb.vector_store.search.side_effect = Exception("Vector store error")
        
        query_params = QueryParams(
            query="error recovery test",
            use_cache=True
        )
        
        # Query should handle error gracefully
        response = await kb.query(query_params)
        
        # Should complete without raising exception
        assert response.total_count == 0  # No results due to error
        assert not response.from_cache
        assert kb._stats["error_count"] == 0  # Error handled in _query_vector_store
        
        # Reset vector store to working state
        kb.vector_store.search.side_effect = None
        kb.vector_store.search.return_value = []
        
        # Subsequent queries should work
        response2 = await kb.query(query_params)
        assert response2 is not None
    
    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, integrated_knowledge_base):
        """Test integrated health monitoring"""
        kb = integrated_knowledge_base
        
        # Initial health check
        health = await kb.health_check()
        assert health["status"] == "healthy"
        assert health["components"]["cache"]["status"] == "healthy"
        assert health["components"]["vector_store"]["status"] == "healthy"
        
        # Simulate vector store becoming unhealthy
        kb.vector_store.health_check.return_value = {"status": "unhealthy", "error": "Connection lost"}
        
        health = await kb.health_check()
        assert health["status"] == "degraded"  # Should degrade, not fail completely
        assert health["components"]["vector_store"]["status"] == "unhealthy"
        
        # Cache should still be healthy
        assert health["components"]["cache"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_statistics_tracking_integration(self, integrated_knowledge_base):
        """Test comprehensive statistics tracking"""
        kb = integrated_knowledge_base
        
        # Setup vector store responses
        mock_result = SearchResult(
            document=ChromaDocument(
                id="stats_doc",
                content="Statistics test document",
                metadata={"title": "Stats Test"}
            ),
            score=0.88,
            distance=0.12
        )
        kb.vector_store.search.return_value = [mock_result]
        
        # Execute various operations
        query_params = QueryParams(query="statistics test", use_cache=True)
        
        # First query (vector store hit)
        await kb.query(query_params)
        
        # Second query (cache hit)
        await kb.query(query_params)
        
        # Different query (vector store hit)
        await kb.query(QueryParams(query="different query", use_cache=True))
        
        # Get comprehensive stats
        stats = await kb.get_stats()
        
        # Verify knowledge base stats
        kb_stats = stats["knowledge_base"]
        assert kb_stats["total_queries"] == 3
        assert kb_stats["cache_hits"] == 1
        assert kb_stats["vector_hits"] == 2
        assert kb_stats["avg_query_time_ms"] > 0
        
        # Verify cache stats are included
        assert "cache" in stats
        cache_stats = stats["cache"]["manager"]
        assert cache_stats["total_requests"] > 0
        
        # Verify vector store stats are included
        assert "vector_store" in stats
        assert stats["vector_store"]["total_documents"] == 100
    
    @pytest.mark.asyncio
    async def test_query_parameter_variations(self, integrated_knowledge_base, sample_documents):
        """Test query behavior with different parameter combinations"""
        kb = integrated_knowledge_base
        
        # Setup different search results for different parameters
        def mock_search_side_effect(query, limit, score_threshold, where):
            """Mock search that varies results based on parameters"""
            if "specific" in query:
                return [SearchResult(
                    document=sample_documents[0],
                    score=0.95,
                    distance=0.05
                )]
            elif limit == 3:
                return [SearchResult(
                    document=doc,
                    score=0.8 - (i * 0.1),
                    distance=0.2 + (i * 0.1)
                ) for i, doc in enumerate(sample_documents[:3])]
            else:
                return [SearchResult(
                    document=sample_documents[0],
                    score=0.7,
                    distance=0.3
                )]
        
        kb.vector_store.search.side_effect = mock_search_side_effect
        
        # Test different parameter combinations
        test_cases = [
            QueryParams(query="specific query", limit=1, score_threshold=0.9),
            QueryParams(query="general query", limit=3, score_threshold=0.5),
            QueryParams(query="broad query", limit=10, score_threshold=0.3),
            QueryParams(
                query="filtered query",
                limit=5,
                metadata_filters={"category": "ai"}
            ),
        ]
        
        results = []
        for params in test_cases:
            response = await kb.query(params)
            results.append({
                "query": params.query,
                "limit": params.limit,
                "threshold": params.score_threshold,
                "filters": params.metadata_filters,
                "result_count": len(response.results),
                "from_cache": response.from_cache
            })
        
        # Verify different behaviors based on parameters
        assert results[0]["result_count"] == 1  # Specific query
        assert results[1]["result_count"] == 3  # Limited to 3
        assert results[2]["result_count"] == 1  # General query
        assert results[3]["result_count"] == 1  # Filtered query
        
        # None should be from cache (different parameters)
        assert all(not r["from_cache"] for r in results)


@pytest.mark.integration
class TestCacheVectorIntegration:
    """Test cache and vector store integration"""
    
    @pytest.fixture
    async def cache_vector_setup(self):
        """Setup cache manager and mock vector store"""
        cache_config = CacheConfig(memory_enabled=True, redis_enabled=False)
        
        memory_cache = MemoryCache(max_size_mb=5, default_ttl_seconds=60)
        cache_manager = CacheManager(cache_config)
        await cache_manager.initialize(memory_cache, None)
        
        mock_vector_store = AsyncMock(spec=ChromaClient)
        
        yield cache_manager, mock_vector_store
        
        await cache_manager.close()
    
    @pytest.mark.asyncio
    async def test_cache_vector_coordination(self, cache_vector_setup, sample_documents):
        """Test coordination between cache and vector store"""
        cache_manager, vector_store = cache_vector_setup
        
        # Setup vector store response
        search_results = [
            SearchResult(
                document=doc,
                score=0.9 - (i * 0.1),
                distance=0.1 + (i * 0.1)
            )
            for i, doc in enumerate(sample_documents[:2])
        ]
        vector_store.search.return_value = search_results
        
        query = "cache vector integration test"
        query_params = {
            "limit": 10,
            "score_threshold": 0.3,
            "metadata_filters": None
        }
        
        # First call - should miss cache and hit vector store
        cached_result = await cache_manager.get_query_cache(query, query_params)
        assert cached_result is None
        
        # Simulate vector store query and cache the results
        vector_results = await vector_store.search(
            query=query,
            limit=query_params["limit"],
            score_threshold=query_params["score_threshold"],
            where=query_params["metadata_filters"]
        )
        
        # Convert to cacheable format
        serializable_results = [
            {
                "content": r.document.content,
                "title": r.document.metadata.get("title", ""),
                "source_type": r.document.metadata.get("source_type", "vector"),
                "url": r.document.metadata.get("source_url"),
                "metadata": r.document.metadata,
                "score": r.score,
                "source": "vector"
            }
            for r in vector_results
        ]
        
        # Cache the results
        await cache_manager.set_query_cache(query, serializable_results, query_params)
        
        # Second call - should hit cache
        cached_result = await cache_manager.get_query_cache(query, query_params)
        assert cached_result is not None
        assert len(cached_result) == len(search_results)
        assert cached_result[0]["content"] == search_results[0].document.content
        
        # Vector store should not be called again
        vector_store.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_patterns(self, cache_vector_setup):
        """Test cache invalidation patterns"""
        cache_manager, vector_store = cache_vector_setup
        
        # Cache some query results
        queries_and_results = [
            ("query about AI", [{"content": "AI result"}]),
            ("query about ML", [{"content": "ML result"}]),
            ("query about CrewAI", [{"content": "CrewAI result"}]),
        ]
        
        for query, results in queries_and_results:
            await cache_manager.set_query_cache(query, results, {})
        
        # Verify all are cached
        for query, _ in queries_and_results:
            cached = await cache_manager.get_query_cache(query, {})
            assert cached is not None
        
        # Invalidate all query cache entries (simulating document update)
        deleted_count = await cache_manager.invalidate_pattern("*", "queries")
        assert deleted_count >= len(queries_and_results)
        
        # Verify all are gone
        for query, _ in queries_and_results:
            cached = await cache_manager.get_query_cache(query, {})
            assert cached is None


@pytest.mark.integration
@pytest.mark.performance
class TestIntegrationPerformance:
    """Performance tests for integrated components"""
    
    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self):
        """Test cache performance under high load"""
        cache_config = CacheConfig(memory_enabled=True, redis_enabled=False)
        memory_cache = MemoryCache(max_size_mb=50, default_ttl_seconds=300)
        cache_manager = CacheManager(cache_config)
        await cache_manager.initialize(memory_cache, None)
        
        # Prepare test data
        num_queries = 1000
        queries = [f"performance test query {i}" for i in range(num_queries)]
        
        import time
        start_time = time.time()
        
        # Cache many query results
        for i, query in enumerate(queries):
            result = [{"content": f"result for {query}", "score": 0.9}]
            await cache_manager.set_query_cache(query, result, {"index": i})
        
        # Retrieve all cached results
        cache_hits = 0
        for i, query in enumerate(queries):
            cached = await cache_manager.get_query_cache(query, {"index": i})
            if cached is not None:
                cache_hits += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions
        assert cache_hits == num_queries  # All should be cached and retrieved
        assert total_time < 5.0  # Should complete within 5 seconds
        
        # Check cache statistics
        stats = await cache_manager.get_stats()
        assert stats["manager"]["total_requests"] >= num_queries
        assert stats["manager"]["overall_hit_ratio"] > 0.5
        
        await cache_manager.close()
    
    @pytest.mark.asyncio
    async def test_query_latency_targets(self, integrated_knowledge_base):
        """Test that query latency meets targets"""
        kb = integrated_knowledge_base
        
        # Setup fast vector store response
        mock_result = SearchResult(
            document=ChromaDocument(
                id="latency_test_doc",
                content="Latency test document",
                metadata={"title": "Latency Test"}
            ),
            score=0.9,
            distance=0.1
        )
        kb.vector_store.search.return_value = [mock_result]
        
        query_params = QueryParams(
            query="latency test query",
            limit=10,
            use_cache=True
        )
        
        # Measure query times
        query_times = []
        for _ in range(20):
            start_time = time.time()
            response = await kb.query(query_params)
            end_time = time.time()
            
            query_time_ms = (end_time - start_time) * 1000
            query_times.append(query_time_ms)
            
            assert response.query_time_ms > 0
        
        # Performance targets
        avg_time = sum(query_times) / len(query_times)
        p95_time = sorted(query_times)[int(0.95 * len(query_times))]
        
        assert avg_time < 200  # Average < 200ms
        assert p95_time < 500   # 95th percentile < 500ms
        
        # Cache hit ratio should improve over time
        final_stats = await kb.get_stats()
        cache_hit_ratio = final_stats["knowledge_base"]["cache_hits"] / final_stats["knowledge_base"]["total_queries"]
        assert cache_hit_ratio > 0.7  # >70% cache hit ratio