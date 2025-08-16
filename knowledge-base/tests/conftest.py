"""Pytest configuration and shared fixtures for Knowledge Base tests"""

import os
import pytest
import asyncio
import uuid
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock
import structlog

# Configure structlog for testing
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_document():
    """Create a sample ChromaDocument for testing"""
    from src.storage import ChromaDocument
    
    return ChromaDocument(
        id=str(uuid.uuid4()),
        content="This is a sample document about AI agents and CrewAI framework for testing purposes.",
        metadata={
            "title": "Sample AI Document",
            "source_type": "test",
            "source_url": "https://example.com/test-doc",
            "author": "Test Author",
            "created_at": "2025-01-01T00:00:00Z",
            "tags": ["ai", "crewai", "test"]
        }
    )


@pytest.fixture
def sample_documents():
    """Create multiple sample documents for testing"""
    from src.storage import ChromaDocument
    
    documents = []
    for i in range(5):
        doc = ChromaDocument(
            id=f"test-doc-{i}",
            content=f"This is test document number {i} about AI and machine learning concepts.",
            metadata={
                "title": f"Test Document {i}",
                "source_type": "test",
                "source_url": f"https://example.com/doc-{i}",
                "category": "ai" if i % 2 == 0 else "ml",
                "priority": i % 3
            }
        )
        documents.append(doc)
    
    return documents


@pytest.fixture
def sample_query_params():
    """Create sample query parameters"""
    from src.knowledge_engine import QueryParams, QuerySource
    
    return QueryParams(
        query="What is CrewAI and how does it work?",
        limit=10,
        score_threshold=0.35,
        sources=[QuerySource.CACHE, QuerySource.VECTOR],
        use_cache=True,
        metadata_filters={"category": "ai"}
    )


@pytest.fixture
def sample_knowledge_results():
    """Create sample knowledge results"""
    from src.knowledge_engine import KnowledgeResult, QuerySource
    
    results = []
    for i in range(3):
        result = KnowledgeResult(
            content=f"Sample result content {i}",
            title=f"Result Title {i}",
            source_type="test",
            url=f"https://example.com/result-{i}",
            metadata={"category": "ai", "index": i},
            score=0.9 - (i * 0.1),
            source=QuerySource.VECTOR
        )
        results.append(result)
    
    return results


@pytest.fixture
def cache_config():
    """Create cache configuration for testing"""
    from src.cache import CacheConfig
    
    return CacheConfig(
        memory_enabled=True,
        redis_enabled=True,
        memory_ttl=300,
        redis_ttl=3600
    )


@pytest.fixture
def mock_memory_cache():
    """Create mock memory cache"""
    from src.cache import MemoryCache
    
    mock = AsyncMock(spec=MemoryCache)
    mock.get.return_value = None
    mock.set.return_value = None
    mock.delete.return_value = True
    mock.clear.return_value = None
    mock.keys.return_value = set()
    mock.get_stats.return_value = {
        "hits": 10,
        "misses": 5,
        "evictions": 2,
        "entries_count": 50,
        "estimated_size_mb": 2.5,
        "hit_ratio": 0.67
    }
    mock.health_check.return_value = {
        "status": "healthy",
        "operations": "ok"
    }
    mock.close.return_value = None
    return mock


@pytest.fixture
def mock_redis_cache():
    """Create mock Redis cache"""
    from src.cache import RedisCache
    
    mock = AsyncMock(spec=RedisCache)
    mock.initialize.return_value = None
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.delete_pattern.return_value = 0
    mock.clear.return_value = True
    mock.exists.return_value = False
    mock.ttl.return_value = -2
    mock.keys.return_value = []
    mock.get_stats.return_value = {
        "hits": 20,
        "misses": 3,
        "sets": 15,
        "deletes": 2,
        "errors": 0,
        "hit_ratio": 0.87,
        "status": "connected",
        "used_memory_mb": 15.5,
        "our_keys_count": 25
    }
    mock.health_check.return_value = {
        "status": "healthy",
        "operations": "ok"
    }
    mock.close.return_value = None
    return mock


@pytest.fixture
def mock_chroma_client():
    """Create mock Chroma client"""
    from src.storage import ChromaClient, SearchResult
    
    mock = AsyncMock(spec=ChromaClient)
    mock.initialize.return_value = None
    mock.add_documents.return_value = None
    mock.update_document.return_value = None
    mock.delete_document.return_value = None
    mock.search.return_value = []
    mock.get_document.return_value = None
    mock.get_collection_stats.return_value = {
        "total_documents": 100,
        "collection_name": "test_collection",
        "embedding_model": "all-MiniLM-L6-v2",
        "similarity_metric": "cosine",
        "queries_total": 50,
        "documents_added": 100,
        "documents_updated": 5,
        "avg_query_time_ms": 25.5
    }
    mock.health_check.return_value = {
        "status": "healthy",
        "connection": "ok",
        "collection_exists": True
    }
    mock.close.return_value = None
    return mock


@pytest.fixture
def mock_search_results(sample_documents):
    """Create mock search results"""
    from src.storage import SearchResult
    
    results = []
    for i, doc in enumerate(sample_documents[:3]):
        result = SearchResult(
            document=doc,
            score=0.9 - (i * 0.1),
            distance=0.1 + (i * 0.1)
        )
        results.append(result)
    
    return results


@pytest.fixture
async def initialized_cache_manager(cache_config, mock_memory_cache, mock_redis_cache):
    """Create initialized cache manager for testing"""
    from src.cache import CacheManager
    
    manager = CacheManager(cache_config)
    await manager.initialize(mock_memory_cache, mock_redis_cache)
    return manager


@pytest.fixture
async def mock_knowledge_base(cache_config, mock_chroma_client):
    """Create mock knowledge base for testing"""
    from src.knowledge_engine import CrewAIKnowledgeBase
    
    kb = CrewAIKnowledgeBase(
        cache_config=cache_config,
        chroma_host="localhost",
        chroma_port=8000,
        redis_url="redis://localhost:6379"
    )
    
    # Replace with mocks
    kb.vector_store = mock_chroma_client
    
    return kb


@pytest.fixture
def performance_test_data():
    """Create data for performance testing"""
    return {
        "queries": [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "Explain neural networks",
            "What are transformer models?",
            "How to implement AI agents?"
        ] * 20,  # 100 queries total
        "expected_latency_ms": 200,
        "expected_cache_hit_ratio": 0.7,
        "concurrent_users": 10
    }


@pytest.fixture
def edge_case_data():
    """Create edge case test data"""
    return {
        "empty_query": "",
        "very_long_query": "What is " * 1000,  # Very long query
        "special_chars_query": "What is AI? How does it work! @#$%^&*()",
        "unicode_query": "What is AI? 人工智能是什么？",
        "null_metadata": None,
        "large_metadata": {"key_" + str(i): f"value_{i}" for i in range(1000)},
        "invalid_score_threshold": -1.5,
        "invalid_limit": -5
    }


# Performance testing utilities
class PerformanceTracker:
    """Track performance metrics during tests"""
    
    def __init__(self):
        self.query_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = 0
    
    def record_query_time(self, time_ms: float):
        self.query_times.append(time_ms)
    
    def record_cache_hit(self):
        self.cache_hits += 1
    
    def record_cache_miss(self):
        self.cache_misses += 1
    
    def record_error(self):
        self.errors += 1
    
    @property
    def avg_query_time(self) -> float:
        return sum(self.query_times) / len(self.query_times) if self.query_times else 0
    
    @property
    def cache_hit_ratio(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0
    
    @property
    def p95_query_time(self) -> float:
        if not self.query_times:
            return 0
        sorted_times = sorted(self.query_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index]


@pytest.fixture
def performance_tracker():
    """Create performance tracker for tests"""
    return PerformanceTracker()


# Error simulation utilities
class ErrorSimulator:
    """Simulate various error conditions"""
    
    @staticmethod
    def network_error():
        from aioredis.exceptions import ConnectionError
        return ConnectionError("Simulated network error")
    
    @staticmethod
    def timeout_error():
        import asyncio
        return asyncio.TimeoutError("Simulated timeout")
    
    @staticmethod
    def serialization_error():
        return TypeError("Object of type 'set' is not JSON serializable")
    
    @staticmethod
    def memory_error():
        return MemoryError("Simulated memory exhaustion")


@pytest.fixture
def error_simulator():
    """Create error simulator for tests"""
    return ErrorSimulator()


# Test data validation utilities
def validate_query_response(response, expected_count: int = None):
    """Validate query response structure"""
    assert hasattr(response, 'results')
    assert hasattr(response, 'total_count')
    assert hasattr(response, 'query_time_ms')
    assert hasattr(response, 'from_cache')
    assert hasattr(response, 'sources_used')
    assert hasattr(response, 'query_params')
    
    assert isinstance(response.results, list)
    assert isinstance(response.total_count, int)
    assert isinstance(response.query_time_ms, (int, float))
    assert isinstance(response.from_cache, bool)
    assert isinstance(response.sources_used, list)
    
    if expected_count is not None:
        assert response.total_count == expected_count
        assert len(response.results) == expected_count


def validate_knowledge_result(result):
    """Validate knowledge result structure"""
    assert hasattr(result, 'content')
    assert hasattr(result, 'title')
    assert hasattr(result, 'source_type')
    assert hasattr(result, 'url')
    assert hasattr(result, 'metadata')
    assert hasattr(result, 'score')
    assert hasattr(result, 'source')
    
    assert isinstance(result.content, str)
    assert isinstance(result.title, str)
    assert isinstance(result.source_type, str)
    assert isinstance(result.metadata, dict)
    assert isinstance(result.score, (int, float))
    assert 0 <= result.score <= 1