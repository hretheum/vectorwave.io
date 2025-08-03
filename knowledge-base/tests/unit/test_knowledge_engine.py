"""Unit tests for CrewAI Knowledge Engine"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from src.knowledge_engine import (
    CrewAIKnowledgeBase, 
    QueryParams, 
    QueryResponse, 
    QuerySource,
    KnowledgeResult
)
from src.cache import CacheConfig
from src.storage import ChromaDocument, SearchResult


@pytest.mark.unit
class TestCrewAIKnowledgeBase:
    """Test CrewAI Knowledge Base main functionality"""
    
    @pytest.fixture
    def knowledge_base(self):
        """Create knowledge base instance"""
        cache_config = CacheConfig(
            memory_enabled=True,
            redis_enabled=True,
            memory_ttl=300,
            redis_ttl=3600
        )
        return CrewAIKnowledgeBase(
            cache_config=cache_config,
            chroma_host="localhost",
            chroma_port=8000,
            redis_url="redis://localhost:6379"
        )
    
    def test_initialization_parameters(self, knowledge_base):
        """Test knowledge base initialization parameters"""
        assert knowledge_base.chroma_host == "localhost"
        assert knowledge_base.chroma_port == 8000
        assert knowledge_base.redis_url == "redis://localhost:6379"
        assert knowledge_base.cache_config is not None
        
        # Check initial state
        assert knowledge_base.cache_manager is None
        assert knowledge_base.vector_store is None
        
        # Check initial stats
        expected_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "vector_hits": 0,
            "markdown_hits": 0,
            "web_hits": 0,
            "avg_query_time_ms": 0.0,
            "error_count": 0
        }
        assert knowledge_base._stats == expected_stats
        
        # Check initial health
        assert knowledge_base._health["status"] == "initializing"
        assert knowledge_base._health["cache"] == "unknown"
        assert knowledge_base._health["vector_store"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, knowledge_base):
        """Test successful initialization"""
        with patch.object(knowledge_base, '_initialize_cache') as mock_cache_init, \
             patch.object(knowledge_base, '_initialize_vector_store') as mock_vector_init:
            
            mock_cache_init.return_value = None
            mock_vector_init.return_value = None
            
            await knowledge_base.initialize()
            
            assert knowledge_base._health["status"] == "healthy"
            assert knowledge_base._health["last_check"] is not None
            
            mock_cache_init.assert_called_once()
            mock_vector_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, knowledge_base):
        """Test initialization failure"""
        with patch.object(knowledge_base, '_initialize_cache', side_effect=Exception("Cache error")):
            
            with pytest.raises(Exception, match="Cache error"):
                await knowledge_base.initialize()
            
            assert knowledge_base._health["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, knowledge_base):
        """Test cache initialization"""
        with patch('src.cache.MemoryCache') as mock_memory_cache, \
             patch('src.cache.RedisCache') as mock_redis_cache, \
             patch('src.cache.CacheManager') as mock_cache_manager:
            
            mock_manager_instance = AsyncMock()
            mock_cache_manager.return_value = mock_manager_instance
            
            await knowledge_base._initialize_cache()
            
            assert knowledge_base.cache_manager == mock_manager_instance
            assert knowledge_base._health["cache"] == "healthy"
            
            mock_manager_instance.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_initialization_failure(self, knowledge_base):
        """Test cache initialization failure (should not raise)"""
        with patch('src.cache.CacheManager', side_effect=Exception("Cache failed")):
            
            # Should not raise exception (cache is optional)
            await knowledge_base._initialize_cache()
            
            assert knowledge_base._health["cache"] == "unhealthy"
            assert knowledge_base.cache_manager is None
    
    @pytest.mark.asyncio
    async def test_vector_store_initialization(self, knowledge_base):
        """Test vector store initialization"""
        with patch('src.storage.ChromaClient') as mock_chroma_client:
            
            mock_client_instance = AsyncMock()
            mock_chroma_client.return_value = mock_client_instance
            
            await knowledge_base._initialize_vector_store()
            
            assert knowledge_base.vector_store == mock_client_instance
            assert knowledge_base._health["vector_store"] == "healthy"
            
            mock_client_instance.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_vector_store_initialization_failure(self, knowledge_base):
        """Test vector store initialization failure (should not raise)"""
        with patch('src.storage.ChromaClient', side_effect=Exception("Vector store failed")):
            
            # Should not raise exception (can fallback to other sources)
            await knowledge_base._initialize_vector_store()
            
            assert knowledge_base._health["vector_store"] == "unhealthy"
            assert knowledge_base.vector_store is None
    
    @pytest.mark.asyncio
    async def test_query_cache_hit(self, knowledge_base, sample_query_params, sample_knowledge_results):
        """Test query with cache hit"""
        # Setup mocks
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get_query_cache.return_value = [
            {
                "content": result.content,
                "title": result.title,
                "source_type": result.source_type,
                "url": result.url,
                "metadata": result.metadata,
                "score": result.score,
                "source": result.source.value
            }
            for result in sample_knowledge_results
        ]
        knowledge_base.cache_manager = mock_cache_manager
        
        response = await knowledge_base.query(sample_query_params)
        
        assert response.from_cache is True
        assert len(response.results) == len(sample_knowledge_results)
        assert QuerySource.CACHE in response.sources_used
        assert knowledge_base._stats["cache_hits"] == 1
        assert knowledge_base._stats["total_queries"] == 1
    
    @pytest.mark.asyncio
    async def test_query_vector_store_hit(self, knowledge_base, sample_query_params, mock_search_results):
        """Test query with vector store hit"""
        # Setup mocks
        knowledge_base.cache_manager = AsyncMock()
        knowledge_base.cache_manager.get_query_cache.return_value = None  # Cache miss
        
        mock_vector_store = AsyncMock()
        mock_vector_store.search.return_value = mock_search_results
        knowledge_base.vector_store = mock_vector_store
        
        # Disable cache for this test
        sample_query_params.use_cache = False
        
        response = await knowledge_base.query(sample_query_params)
        
        assert response.from_cache is False
        assert len(response.results) == len(mock_search_results)
        assert QuerySource.VECTOR in response.sources_used
        assert knowledge_base._stats["vector_hits"] == 1
        assert knowledge_base._stats["total_queries"] == 1
    
    @pytest.mark.asyncio
    async def test_query_fallback_strategy(self, knowledge_base, sample_query_params):
        """Test fallback strategy when cache and vector store fail"""
        # Setup mocks - all return empty/None
        knowledge_base.cache_manager = AsyncMock()
        knowledge_base.cache_manager.get_query_cache.return_value = None
        
        knowledge_base.vector_store = AsyncMock()
        knowledge_base.vector_store.search.return_value = []
        
        response = await knowledge_base.query(sample_query_params)
        
        assert response.from_cache is False
        assert len(response.results) == 0
        assert response.total_count == 0
        assert knowledge_base._stats["total_queries"] == 1
    
    @pytest.mark.asyncio
    async def test_query_with_specific_sources(self, knowledge_base):
        """Test query with specific source selection"""
        params = QueryParams(
            query="test query",
            sources=[QuerySource.VECTOR],  # Only vector source
            use_cache=True
        )
        
        # Setup mocks
        knowledge_base.cache_manager = AsyncMock()
        knowledge_base.vector_store = AsyncMock()
        knowledge_base.vector_store.search.return_value = []
        
        await knowledge_base.query(params)
        
        # Should only try vector store, not cache
        knowledge_base.cache_manager.get_query_cache.assert_not_called()
        knowledge_base.vector_store.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_caching_results(self, knowledge_base, sample_query_params, mock_search_results):
        """Test that successful query results are cached"""
        # Setup mocks
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get_query_cache.return_value = None  # Cache miss
        knowledge_base.cache_manager = mock_cache_manager
        
        mock_vector_store = AsyncMock()
        mock_vector_store.search.return_value = mock_search_results
        knowledge_base.vector_store = mock_vector_store
        
        response = await knowledge_base.query(sample_query_params)
        
        # Should cache the results
        mock_cache_manager.set_query_cache.assert_called_once()
        call_args = mock_cache_manager.set_query_cache.call_args
        assert call_args[0][0] == sample_query_params.query  # query
        assert len(call_args[0][1]) == len(mock_search_results)  # results
    
    @pytest.mark.asyncio
    async def test_query_error_handling(self, knowledge_base, sample_query_params):
        """Test query error handling"""
        # Setup mock that raises exception
        knowledge_base.cache_manager = AsyncMock()
        knowledge_base.cache_manager.get_query_cache.side_effect = Exception("Cache error")
        
        with pytest.raises(Exception, match="Cache error"):
            await knowledge_base.query(sample_query_params)
        
        assert knowledge_base._stats["error_count"] == 1
    
    @pytest.mark.asyncio
    async def test_add_document_success(self, knowledge_base, sample_document):
        """Test successful document addition"""
        mock_vector_store = AsyncMock()
        mock_vector_store.add_documents.return_value = None
        knowledge_base.vector_store = mock_vector_store
        
        mock_cache_manager = AsyncMock()
        knowledge_base.cache_manager = mock_cache_manager
        
        success = await knowledge_base.add_document(sample_document)
        
        assert success is True
        mock_vector_store.add_documents.assert_called_once_with([sample_document])
        mock_cache_manager.invalidate_pattern.assert_called_once_with("*", "queries")
    
    @pytest.mark.asyncio
    async def test_add_document_no_vector_store(self, knowledge_base, sample_document):
        """Test document addition without vector store"""
        knowledge_base.vector_store = None
        
        success = await knowledge_base.add_document(sample_document)
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_add_document_error(self, knowledge_base, sample_document):
        """Test document addition error handling"""
        mock_vector_store = AsyncMock()
        mock_vector_store.add_documents.side_effect = Exception("Add error")
        knowledge_base.vector_store = mock_vector_store
        
        success = await knowledge_base.add_document(sample_document)
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_update_document_success(self, knowledge_base, sample_document):
        """Test successful document update"""
        mock_vector_store = AsyncMock()
        mock_vector_store.update_document.return_value = None
        knowledge_base.vector_store = mock_vector_store
        
        mock_cache_manager = AsyncMock()
        knowledge_base.cache_manager = mock_cache_manager
        
        success = await knowledge_base.update_document(sample_document)
        
        assert success is True
        mock_vector_store.update_document.assert_called_once_with(sample_document)
        mock_cache_manager.invalidate_pattern.assert_called_once_with("*", "queries")
    
    @pytest.mark.asyncio
    async def test_delete_document_success(self, knowledge_base):
        """Test successful document deletion"""
        mock_vector_store = AsyncMock()
        mock_vector_store.delete_document.return_value = None
        knowledge_base.vector_store = mock_vector_store
        
        mock_cache_manager = AsyncMock()
        knowledge_base.cache_manager = mock_cache_manager
        
        success = await knowledge_base.delete_document("test_doc_id")
        
        assert success is True
        mock_vector_store.delete_document.assert_called_once_with("test_doc_id")
        mock_cache_manager.invalidate_pattern.assert_called_once_with("*", "queries")
    
    @pytest.mark.asyncio
    async def test_get_stats(self, knowledge_base):
        """Test getting comprehensive statistics"""
        # Setup mocks
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get_stats.return_value = {"cache": "stats"}
        knowledge_base.cache_manager = mock_cache_manager
        
        mock_vector_store = AsyncMock()
        mock_vector_store.get_collection_stats.return_value = {"vector": "stats"}
        knowledge_base.vector_store = mock_vector_store
        
        stats = await knowledge_base.get_stats()
        
        assert "knowledge_base" in stats
        assert "health" in stats
        assert "cache" in stats
        assert "vector_store" in stats
        assert stats["cache"] == {"cache": "stats"}
        assert stats["vector_store"] == {"vector": "stats"}
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, knowledge_base):
        """Test health check when all components are healthy"""
        # Setup mocks
        mock_cache_manager = AsyncMock()
        mock_cache_manager.health_check.return_value = {"status": "healthy"}
        knowledge_base.cache_manager = mock_cache_manager
        
        mock_vector_store = AsyncMock()
        mock_vector_store.health_check.return_value = {"status": "healthy"}
        knowledge_base.vector_store = mock_vector_store
        
        health = await knowledge_base.health_check()
        
        assert health["status"] == "healthy"
        assert health["components"]["cache"]["status"] == "healthy"
        assert health["components"]["vector_store"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self, knowledge_base):
        """Test health check when one component is unhealthy"""
        # Setup mocks
        mock_cache_manager = AsyncMock()
        mock_cache_manager.health_check.return_value = {"status": "unhealthy"}
        knowledge_base.cache_manager = mock_cache_manager
        
        mock_vector_store = AsyncMock()
        mock_vector_store.health_check.return_value = {"status": "healthy"}
        knowledge_base.vector_store = mock_vector_store
        
        health = await knowledge_base.health_check()
        
        assert health["status"] == "degraded"
    
    @pytest.mark.asyncio
    async def test_health_check_error(self, knowledge_base):
        """Test health check error handling"""
        # Setup mocks that raise exceptions
        mock_cache_manager = AsyncMock()
        mock_cache_manager.health_check.side_effect = Exception("Health check error")
        knowledge_base.cache_manager = mock_cache_manager
        
        health = await knowledge_base.health_check()
        
        assert health["status"] == "unhealthy"
        assert "error" in health
    
    @pytest.mark.asyncio
    async def test_close(self, knowledge_base):
        """Test closing knowledge base"""
        # Setup mocks
        mock_cache_manager = AsyncMock()
        knowledge_base.cache_manager = mock_cache_manager
        
        mock_vector_store = AsyncMock()
        knowledge_base.vector_store = mock_vector_store
        
        await knowledge_base.close()
        
        mock_cache_manager.close.assert_called_once()
        mock_vector_store.close.assert_called_once()
    
    def test_deduplicate_results(self, knowledge_base):
        """Test result deduplication"""
        # Create duplicate results
        results = [
            KnowledgeResult(
                content="Content 1",
                title="Title 1",
                source_type="test",
                url="url1",
                metadata={},
                score=0.9,
                source=QuerySource.VECTOR
            ),
            KnowledgeResult(
                content="Content 2",
                title="Title 1",  # Same title
                source_type="test",  # Same source type
                url="url2",
                metadata={},
                score=0.8,
                source=QuerySource.VECTOR
            ),
            KnowledgeResult(
                content="Content 3",
                title="Title 2",
                source_type="test",
                url="url3",
                metadata={},
                score=0.7,
                source=QuerySource.VECTOR
            )
        ]
        
        deduplicated = knowledge_base._deduplicate_results(results)
        
        # Should remove the duplicate (same title + source_type)
        assert len(deduplicated) == 2
        assert deduplicated[0].title == "Title 1"
        assert deduplicated[1].title == "Title 2"
    
    def test_sort_results(self, knowledge_base):
        """Test result sorting by relevance score"""
        results = [
            KnowledgeResult(
                content="Low score",
                title="Low",
                source_type="test",
                url="url1",
                metadata={},
                score=0.3,
                source=QuerySource.VECTOR
            ),
            KnowledgeResult(
                content="High score",
                title="High",
                source_type="test",
                url="url2",
                metadata={},
                score=0.9,
                source=QuerySource.VECTOR
            ),
            KnowledgeResult(
                content="Medium score",
                title="Medium",
                source_type="test",
                url="url3",
                metadata={},
                score=0.6,
                source=QuerySource.VECTOR
            )
        ]
        
        sorted_results = knowledge_base._sort_results(results)
        
        # Should be sorted by score (highest first)
        assert sorted_results[0].score == 0.9
        assert sorted_results[1].score == 0.6
        assert sorted_results[2].score == 0.3
    
    def test_update_avg_query_time(self, knowledge_base):
        """Test average query time calculation"""
        # First query
        knowledge_base._update_avg_query_time(100.0)
        assert knowledge_base._stats["avg_query_time_ms"] == 100.0
        
        # Second query (should use exponential moving average)
        knowledge_base._update_avg_query_time(200.0)
        expected = 0.1 * 200.0 + 0.9 * 100.0  # alpha=0.1
        assert knowledge_base._stats["avg_query_time_ms"] == expected
    
    @pytest.mark.asyncio
    async def test_query_cache_method(self, knowledge_base, sample_query_params):
        """Test _query_cache method"""
        # No cache manager
        result = await knowledge_base._query_cache(sample_query_params)
        assert result is None
        
        # With cache manager but cache miss
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get_query_cache.return_value = None
        knowledge_base.cache_manager = mock_cache_manager
        
        result = await knowledge_base._query_cache(sample_query_params)
        assert result is None
        
        # With cache hit
        cached_data = [{"content": "cached", "title": "test", "source": "cache"}]
        mock_cache_manager.get_query_cache.return_value = cached_data
        
        result = await knowledge_base._query_cache(sample_query_params)
        assert result is not None
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_query_vector_store_method(self, knowledge_base, sample_query_params, mock_search_results):
        """Test _query_vector_store method"""
        # No vector store
        result = await knowledge_base._query_vector_store(sample_query_params)
        assert result is None
        
        # With vector store
        mock_vector_store = AsyncMock()
        mock_vector_store.search.return_value = mock_search_results
        knowledge_base.vector_store = mock_vector_store
        
        result = await knowledge_base._query_vector_store(sample_query_params)
        assert result is not None
        assert len(result) == len(mock_search_results)
        assert all(isinstance(r, KnowledgeResult) for r in result)
    
    @pytest.mark.asyncio
    async def test_query_markdown_method(self, knowledge_base, sample_query_params):
        """Test _query_markdown method (placeholder)"""
        result = await knowledge_base._query_markdown(sample_query_params)
        assert result is None  # Not implemented yet
    
    @pytest.mark.asyncio
    async def test_query_web_method(self, knowledge_base, sample_query_params):
        """Test _query_web method (placeholder)"""
        result = await knowledge_base._query_web(sample_query_params)
        assert result is None  # Not implemented yet


@pytest.mark.unit
class TestQueryParams:
    """Test QueryParams dataclass"""
    
    def test_default_creation(self):
        """Test creating QueryParams with defaults"""
        params = QueryParams(query="test query")
        
        assert params.query == "test query"
        assert params.limit == 10
        assert params.score_threshold == 0.35
        assert params.sources is None
        assert params.use_cache is True
        assert params.metadata_filters is None
    
    def test_custom_creation(self):
        """Test creating QueryParams with custom values"""
        params = QueryParams(
            query="custom query",
            limit=20,
            score_threshold=0.5,
            sources=[QuerySource.VECTOR],
            use_cache=False,
            metadata_filters={"category": "ai"}
        )
        
        assert params.query == "custom query"
        assert params.limit == 20
        assert params.score_threshold == 0.5
        assert params.sources == [QuerySource.VECTOR]
        assert params.use_cache is False
        assert params.metadata_filters == {"category": "ai"}


@pytest.mark.unit
class TestKnowledgeResult:
    """Test KnowledgeResult dataclass"""
    
    def test_creation(self):
        """Test creating KnowledgeResult"""
        result = KnowledgeResult(
            content="Test content",
            title="Test Title",
            source_type="test",
            url="https://example.com",
            metadata={"key": "value"},
            score=0.85,
            source=QuerySource.VECTOR
        )
        
        assert result.content == "Test content"
        assert result.title == "Test Title"
        assert result.source_type == "test"
        assert result.url == "https://example.com"
        assert result.metadata == {"key": "value"}
        assert result.score == 0.85
        assert result.source == QuerySource.VECTOR


@pytest.mark.unit
class TestQueryResponse:
    """Test QueryResponse dataclass"""
    
    def test_creation(self, sample_knowledge_results, sample_query_params):
        """Test creating QueryResponse"""
        response = QueryResponse(
            results=sample_knowledge_results,
            total_count=len(sample_knowledge_results),
            query_time_ms=150.5,
            from_cache=False,
            sources_used=[QuerySource.VECTOR],
            query_params=sample_query_params
        )
        
        assert response.results == sample_knowledge_results
        assert response.total_count == len(sample_knowledge_results)
        assert response.query_time_ms == 150.5
        assert response.from_cache is False
        assert response.sources_used == [QuerySource.VECTOR]
        assert response.query_params == sample_query_params


@pytest.mark.unit
class TestQuerySource:
    """Test QuerySource enum"""
    
    def test_enum_values(self):
        """Test QuerySource enum values"""
        assert QuerySource.CACHE.value == "cache"
        assert QuerySource.VECTOR.value == "vector"
        assert QuerySource.MARKDOWN.value == "markdown"
        assert QuerySource.WEB.value == "web"
    
    def test_enum_creation_from_string(self):
        """Test creating QuerySource from string"""
        assert QuerySource("cache") == QuerySource.CACHE
        assert QuerySource("vector") == QuerySource.VECTOR
        assert QuerySource("markdown") == QuerySource.MARKDOWN
        assert QuerySource("web") == QuerySource.WEB


@pytest.mark.unit
@pytest.mark.performance
class TestKnowledgeEnginePerformance:
    """Performance tests for Knowledge Engine"""
    
    @pytest.mark.asyncio
    async def test_query_performance(self, knowledge_base, performance_test_data):
        """Test query performance under load"""
        # Setup mocks for fast responses
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get_query_cache.return_value = [
            {"content": "cached result", "title": "test", "source": "cache"}
        ]
        knowledge_base.cache_manager = mock_cache_manager
        
        queries = performance_test_data["queries"]
        start_time = time.time()
        
        # Execute queries
        for query in queries[:10]:  # Test with 10 queries
            params = QueryParams(query=query)
            response = await knowledge_base.query(params)
            assert response.query_time_ms < performance_test_data["expected_latency_ms"]
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Should complete all queries within reasonable time
        avg_time_per_query = total_time / 10
        assert avg_time_per_query < 50  # 50ms per query on average
    
    @pytest.mark.asyncio
    async def test_concurrent_queries(self, knowledge_base):
        """Test concurrent query handling"""
        # Setup mock that returns quickly
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get_query_cache.return_value = [
            {"content": "concurrent result", "title": "test", "source": "cache"}
        ]
        knowledge_base.cache_manager = mock_cache_manager
        
        async def execute_query(query_id):
            params = QueryParams(query=f"concurrent query {query_id}")
            response = await knowledge_base.query(params)
            return response.total_count > 0
        
        # Execute 20 concurrent queries
        tasks = [execute_query(i) for i in range(20)]
        start_time = time.time()
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        # All queries should succeed
        assert all(results)
        
        # Should complete within reasonable time even with concurrency
        total_time = end_time - start_time
        assert total_time < 2.0  # 2 seconds for 20 concurrent queries