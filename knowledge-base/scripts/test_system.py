#!/usr/bin/env python3
"""System Test Script for Knowledge Base"""

import asyncio
import json
import time
from typing import Dict, List
import structlog

from src.knowledge_engine import (
    CrewAIKnowledgeBase, 
    QueryParams, 
    QuerySource
)
from src.cache import CacheConfig
from src.storage import ChromaDocument
from src.sync import CrewAIDocsScraper

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def test_vector_store():
    """Test Chroma DB vector store functionality"""
    logger.info("Testing Vector Store")
    
    try:
        # Initialize knowledge base
        cache_config = CacheConfig(
            memory_enabled=True,
            redis_enabled=False,  # Skip Redis for basic test
            memory_ttl=300
        )
        
        kb = CrewAIKnowledgeBase(
            cache_config=cache_config,
            chroma_host="localhost",
            chroma_port=8000
        )
        
        await kb.initialize()
        
        # Test document addition
        sample_docs = [
            ChromaDocument(
                id="test_doc_1",
                content="CrewAI is a powerful framework for building AI agent workflows. It allows you to create teams of AI agents that can collaborate to solve complex tasks.",
                metadata={
                    "title": "CrewAI Introduction",
                    "source_type": "test",
                    "category": "core-concepts",
                    "tags": ["crewai", "agents", "workflow"]
                }
            ),
            ChromaDocument(
                id="test_doc_2",
                content="To install CrewAI, you can use pip: pip install crewai. Make sure you have Python 3.8 or higher installed on your system.",
                metadata={
                    "title": "CrewAI Installation",
                    "source_type": "test",
                    "category": "installation",
                    "tags": ["installation", "pip", "python"]
                }
            ),
            ChromaDocument(
                id="test_doc_3",
                content="CrewAI agents can use various tools and LLMs. You can configure memory, planning strategies, and custom flows for your agent teams.",
                metadata={
                    "title": "CrewAI Advanced Features",
                    "source_type": "test",
                    "category": "advanced",
                    "tags": ["tools", "llms", "memory", "planning"]
                }
            )
        ]
        
        # Add documents
        for doc in sample_docs:
            success = await kb.add_document(doc)
            if success:
                logger.info("Document added", doc_id=doc.id)
            else:
                logger.error("Failed to add document", doc_id=doc.id)
        
        # Test queries
        test_queries = [
            "How to install CrewAI?",
            "What is CrewAI?",
            "agent workflows",
            "memory and planning"
        ]
        
        for query in test_queries:
            logger.info("Testing query", query=query)
            
            params = QueryParams(
                query=query,
                limit=3,
                score_threshold=0.3,
                use_cache=True
            )
            
            response = await kb.query(params)
            
            logger.info(
                "Query results",
                query=query,
                results_count=response.total_count,
                query_time_ms=round(response.query_time_ms, 2),
                from_cache=response.from_cache,
                sources_used=[s.value for s in response.sources_used]
            )
            
            for i, result in enumerate(response.results):
                logger.info(
                    "Result",
                    rank=i+1,
                    title=result.title,
                    score=round(result.score, 3),
                    content_preview=result.content[:100] + "..."
                )
        
        # Test stats
        stats = await kb.get_stats()
        logger.info("Knowledge base stats", stats=stats)
        
        # Test health check
        health = await kb.health_check()
        logger.info("Health check", status=health["status"])
        
        await kb.close()
        logger.info("Vector store test completed successfully")
        return True
        
    except Exception as e:
        logger.error("Vector store test failed", error=str(e))
        return False


async def test_cache_system():
    """Test cache system functionality"""
    logger.info("Testing Cache System")
    
    try:
        from src.cache import MemoryCache, CacheManager
        
        # Test memory cache
        memory_cache = MemoryCache(default_ttl_seconds=60)
        
        # Test basic operations
        await memory_cache.set("test_key", {"data": "test_value"})
        value = await memory_cache.get("test_key")
        assert value["data"] == "test_value"
        
        # Test TTL
        await memory_cache.set("ttl_test", "expires_soon", ttl_seconds=1)
        await asyncio.sleep(2)
        expired_value = await memory_cache.get("ttl_test")
        assert expired_value is None
        
        # Test cache manager
        cache_config = CacheConfig(
            memory_enabled=True,
            redis_enabled=False,  # Skip Redis for basic test
            memory_ttl=300
        )
        
        cache_manager = CacheManager(cache_config)
        await cache_manager.initialize(memory_cache, None)
        
        # Test cache manager operations
        await cache_manager.set("manager_test", {"complex": "data", "numbers": [1, 2, 3]})
        cached_data = await cache_manager.get("manager_test")
        assert cached_data["complex"] == "data"
        
        # Test query cache
        await cache_manager.set_query_cache(
            "test query", 
            [{"result": "data"}],
            {"limit": 10}
        )
        
        query_result = await cache_manager.get_query_cache(
            "test query",
            {"limit": 10}
        )
        assert query_result[0]["result"] == "data"
        
        # Get stats
        stats = await cache_manager.get_stats()
        logger.info("Cache stats", stats=stats)
        
        # Health check
        health = await cache_manager.health_check()
        assert health["status"] == "healthy"
        
        await cache_manager.close()
        logger.info("Cache system test completed successfully")
        return True
        
    except Exception as e:
        logger.error("Cache system test failed", error=str(e))
        return False


async def test_docs_scraper():
    """Test documentation scraper (mock test)"""
    logger.info("Testing Documentation Scraper")
    
    try:
        # Create scraper with mock settings
        scraper = CrewAIDocsScraper(
            base_url="https://docs.crewai.com",
            timeout_seconds=10,
            max_concurrent=2,
            rate_limit_delay=0.5
        )
        
        await scraper.initialize()
        
        # Test URL validation
        assert scraper._is_documentation_url("https://docs.crewai.com/core-concepts/")
        assert not scraper._is_documentation_url("https://docs.crewai.com/api/admin/")
        assert not scraper._is_documentation_url("https://external-site.com/")
        
        # Test hash generation consistency
        content1 = "This is test content for hashing"
        content2 = "This is test content for hashing"
        content3 = "This is different content"
        
        import hashlib
        hash1 = hashlib.sha256(content1.encode()).hexdigest()
        hash2 = hashlib.sha256(content2.encode()).hexdigest()
        hash3 = hashlib.sha256(content3.encode()).hexdigest()
        
        assert hash1 == hash2
        assert hash1 != hash3
        
        # Get stats
        stats = await scraper.get_stats()
        logger.info("Scraper stats", stats=stats)
        
        await scraper.close()
        logger.info("Documentation scraper test completed successfully")
        return True
        
    except Exception as e:
        logger.error("Documentation scraper test failed", error=str(e))
        return False


async def test_integration():
    """Test full integration with all components"""
    logger.info("Testing Full Integration")
    
    try:
        # Create knowledge base with all features
        cache_config = CacheConfig(
            memory_enabled=True,
            redis_enabled=False,  # Skip Redis for basic test
            memory_ttl=300,
            redis_ttl=3600
        )
        
        kb = CrewAIKnowledgeBase(
            cache_config=cache_config,
            chroma_host="localhost",
            chroma_port=8000
        )
        
        await kb.initialize()
        
        # Add comprehensive test documents
        docs = [
            ChromaDocument(
                id="integration_doc_1",
                content="CrewAI provides a comprehensive framework for multi-agent workflows. Agents can be configured with specific roles, goals, and backstories to create powerful AI teams.",
                metadata={
                    "title": "Multi-Agent Workflows",
                    "source_type": "integration_test",
                    "category": "core-concepts",
                    "difficulty": "intermediate",
                    "tags": ["agents", "workflow", "roles"]
                }
            ),
            ChromaDocument(
                id="integration_doc_2",
                content="Setting up CrewAI involves installing the package via pip, configuring your environment variables for LLM access, and creating your first agent team with defined tasks.",
                metadata={
                    "title": "CrewAI Setup Guide",
                    "source_type": "integration_test",
                    "category": "installation",
                    "difficulty": "beginner",
                    "tags": ["setup", "installation", "configuration"]
                }
            )
        ]
        
        # Add documents
        for doc in docs:
            await kb.add_document(doc)
        
        # Test different query scenarios
        test_scenarios = [
            {
                "name": "Basic search",
                "params": QueryParams(
                    query="multi-agent workflows",
                    limit=5,
                    score_threshold=0.3
                )
            },
            {
                "name": "Filtered search by category",
                "params": QueryParams(
                    query="setup",
                    limit=5,
                    score_threshold=0.2,
                    metadata_filters={"category": "installation"}
                )
            },
            {
                "name": "Vector-only search",
                "params": QueryParams(
                    query="agent configuration",
                    limit=3,
                    sources=[QuerySource.VECTOR],
                    use_cache=False
                )
            },
            {
                "name": "Cached search (second run)",
                "params": QueryParams(
                    query="multi-agent workflows",  # Same as first query
                    limit=5,
                    score_threshold=0.3
                )
            }
        ]
        
        for scenario in test_scenarios:
            logger.info("Running scenario", name=scenario["name"])
            
            start_time = time.time()
            response = await kb.query(scenario["params"])
            duration = time.time() - start_time
            
            logger.info(
                "Scenario results",
                name=scenario["name"],
                results_count=response.total_count,
                query_time_ms=round(response.query_time_ms, 2),
                total_duration_ms=round(duration * 1000, 2),
                from_cache=response.from_cache,
                sources_used=[s.value for s in response.sources_used]
            )
            
            # Verify cache behavior
            if scenario["name"] == "Cached search (second run)":
                if not response.from_cache:
                    logger.warning("Expected cache hit but got cache miss")
        
        # Test system health and stats
        health = await kb.health_check()
        stats = await kb.get_stats()
        
        logger.info(
            "Integration test completed",
            health_status=health["status"],
            total_queries=stats["knowledge_base"]["total_queries"],
            cache_hits=stats["knowledge_base"]["cache_hits"]
        )
        
        await kb.close()
        return True
        
    except Exception as e:
        logger.error("Integration test failed", error=str(e))
        return False


async def run_performance_test():
    """Run basic performance tests"""
    logger.info("Running Performance Tests")
    
    try:
        cache_config = CacheConfig(
            memory_enabled=True,
            redis_enabled=False,
            memory_ttl=300
        )
        
        kb = CrewAIKnowledgeBase(cache_config=cache_config)
        await kb.initialize()
        
        # Add multiple documents for performance testing
        docs = []
        for i in range(50):
            docs.append(ChromaDocument(
                id=f"perf_doc_{i}",
                content=f"This is performance test document {i}. It contains information about CrewAI features, agent configuration, and workflow management. Document {i} has unique content for testing search relevance.",
                metadata={
                    "title": f"Performance Test Doc {i}",
                    "source_type": "performance_test",
                    "category": "testing",
                    "doc_number": i
                }
            ))
        
        # Batch add documents
        if kb.vector_store:
            await kb.vector_store.add_documents(docs)
        
        # Performance test queries
        query_times = []
        cache_hits = 0
        
        test_queries = [
            "CrewAI features",
            "agent configuration",
            "workflow management",
            "performance test",
            "document information"
        ]
        
        # Run multiple query iterations
        for iteration in range(10):
            for query in test_queries:
                start_time = time.time()
                
                params = QueryParams(
                    query=query,
                    limit=10,
                    score_threshold=0.2
                )
                
                response = await kb.query(params)
                
                query_time = (time.time() - start_time) * 1000
                query_times.append(query_time)
                
                if response.from_cache:
                    cache_hits += 1
        
        # Calculate performance metrics
        avg_query_time = sum(query_times) / len(query_times)
        min_query_time = min(query_times)
        max_query_time = max(query_times)
        cache_hit_ratio = cache_hits / len(query_times)
        
        logger.info(
            "Performance test results",
            total_queries=len(query_times),
            avg_query_time_ms=round(avg_query_time, 2),
            min_query_time_ms=round(min_query_time, 2),
            max_query_time_ms=round(max_query_time, 2),
            cache_hit_ratio=round(cache_hit_ratio, 3),
            p95_query_time_ms=round(sorted(query_times)[int(len(query_times) * 0.95)], 2)
        )
        
        # Check performance targets
        success = True
        if avg_query_time > 500:  # Target: <500ms average
            logger.warning("Average query time exceeds target", target=500, actual=avg_query_time)
            success = False
        
        if cache_hit_ratio < 0.3:  # Should have some cache hits after iteration 1
            logger.warning("Cache hit ratio too low", target=0.3, actual=cache_hit_ratio)
            success = False
        
        await kb.close()
        return success
        
    except Exception as e:
        logger.error("Performance test failed", error=str(e))
        return False


async def main():
    """Run all tests"""
    logger.info("Starting Knowledge Base System Tests")
    
    tests = [
        ("Cache System", test_cache_system),
        ("Documentation Scraper", test_docs_scraper),
        ("Vector Store", test_vector_store),
        ("Integration", test_integration),
        ("Performance", run_performance_test),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info("Running test", test=test_name)
        try:
            success = await test_func()
            results[test_name] = "PASS" if success else "FAIL"
            logger.info("Test completed", test=test_name, result=results[test_name])
        except Exception as e:
            results[test_name] = "ERROR"
            logger.error("Test error", test=test_name, error=str(e))
        
        # Brief pause between tests
        await asyncio.sleep(1)
    
    # Summary
    logger.info("Test Summary")
    passed = sum(1 for result in results.values() if result == "PASS")
    total = len(results)
    
    for test_name, result in results.items():
        logger.info("Test result", test=test_name, result=result)
    
    logger.info(
        "Overall results",
        passed=passed,
        total=total,
        success_rate=f"{(passed/total)*100:.1f}%"
    )
    
    if passed == total:
        logger.info("All tests passed! 🎉")
        return True
    else:
        logger.warning("Some tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)