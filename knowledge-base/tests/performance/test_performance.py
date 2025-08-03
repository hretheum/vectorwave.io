"""Performance tests for Knowledge Base components"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock
from src.knowledge_engine import CrewAIKnowledgeBase, QueryParams
from src.cache import CacheManager, CacheConfig, MemoryCache, RedisCache
from src.storage import ChromaClient, ChromaDocument, SearchResult


@pytest.mark.performance
class TestQueryPerformance:
    """Test query performance benchmarks"""
    
    @pytest.fixture
    async def performance_knowledge_base(self):
        """Create optimized knowledge base for performance testing"""
        cache_config = CacheConfig(
            memory_enabled=True,
            redis_enabled=False,  # Use only memory cache for consistent performance
            memory_ttl=3600,
            redis_ttl=7200
        )
        
        kb = CrewAIKnowledgeBase(cache_config=cache_config)
        
        # Use real memory cache for realistic performance
        memory_cache = MemoryCache(max_size_mb=100, default_ttl_seconds=3600)
        cache_manager = CacheManager(cache_config)
        await cache_manager.initialize(memory_cache, None)
        kb.cache_manager = cache_manager
        
        # Mock vector store with realistic response times
        mock_vector_store = AsyncMock(spec=ChromaClient)
        
        async def mock_search(*args, **kwargs):
            # Simulate realistic vector search latency
            await asyncio.sleep(0.01)  # 10ms base latency
            return [
                SearchResult(
                    document=ChromaDocument(
                        id=f"perf_doc_{i}",
                        content=f"Performance test document {i}",
                        metadata={"title": f"Doc {i}", "category": "performance"}
                    ),
                    score=0.9 - (i * 0.1),
                    distance=0.1 + (i * 0.1)
                )
                for i in range(3)
            ]
        
        mock_vector_store.search.side_effect = mock_search
        kb.vector_store = mock_vector_store
        
        kb._health["status"] = "healthy"
        
        yield kb
        
        await kb.close()
    
    @pytest.mark.asyncio
    async def test_query_latency_benchmark(self, performance_knowledge_base, performance_tracker):
        """Benchmark query latency under various conditions"""
        kb = performance_knowledge_base
        
        # Test scenarios with different characteristics
        test_scenarios = [
            {"name": "simple_query", "query": "What is AI?", "limit": 5},
            {"name": "complex_query", "query": "Explain machine learning algorithms and neural networks", "limit": 10},
            {"name": "filtered_query", "query": "AI agents", "limit": 5, "filters": {"category": "ai"}},
            {"name": "high_limit", "query": "search test", "limit": 50},
        ]
        
        results = {}
        
        for scenario in test_scenarios:
            latencies = []
            
            # Run each scenario multiple times
            for _ in range(20):
                params = QueryParams(
                    query=scenario["query"],
                    limit=scenario["limit"],
                    metadata_filters=scenario.get("filters")
                )
                
                start_time = time.time()
                response = await kb.query(params)
                end_time = time.time()
                
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
                
                performance_tracker.record_query_time(latency_ms)
                
                if response.from_cache:
                    performance_tracker.record_cache_hit()
                else:
                    performance_tracker.record_cache_miss()
            
            results[scenario["name"]] = {
                "avg_latency": statistics.mean(latencies),
                "p50_latency": statistics.median(latencies),
                "p95_latency": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "p99_latency": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
                "min_latency": min(latencies),
                "max_latency": max(latencies)
            }
        
        # Performance assertions
        for scenario_name, metrics in results.items():
            assert metrics["avg_latency"] < 200, f"{scenario_name} average latency too high: {metrics['avg_latency']}ms"
            assert metrics["p95_latency"] < 500, f"{scenario_name} P95 latency too high: {metrics['p95_latency']}ms"
            assert metrics["p99_latency"] < 1000, f"{scenario_name} P99 latency too high: {metrics['p99_latency']}ms"
        
        # Cache effectiveness
        assert performance_tracker.cache_hit_ratio > 0.7, f"Cache hit ratio too low: {performance_tracker.cache_hit_ratio}"
        
        print(f"\nQuery Performance Results:")
        for scenario_name, metrics in results.items():
            print(f"{scenario_name}:")
            print(f"  Avg: {metrics['avg_latency']:.2f}ms")
            print(f"  P95: {metrics['p95_latency']:.2f}ms")
            print(f"  P99: {metrics['p99_latency']:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self, performance_knowledge_base):
        """Test performance under concurrent load"""
        kb = performance_knowledge_base
        
        concurrent_levels = [1, 5, 10, 20, 50]
        results = {}
        
        for concurrency in concurrent_levels:
            latencies = []
            
            async def execute_query(query_id):
                start_time = time.time()
                
                params = QueryParams(
                    query=f"concurrent test query {query_id % 5}",  # Some overlap for caching
                    limit=10
                )
                
                response = await kb.query(params)
                
                end_time = time.time()
                return (end_time - start_time) * 1000, response.from_cache
            
            # Execute concurrent queries
            start_time = time.time()
            tasks = [execute_query(i) for i in range(concurrency)]
            query_results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = end_time - start_time
            latencies = [result[0] for result in query_results]
            cache_hits = sum(1 for result in query_results if result[1])
            
            results[concurrency] = {
                "total_time": total_time,
                "avg_latency": statistics.mean(latencies),
                "max_latency": max(latencies),
                "cache_hit_ratio": cache_hits / len(query_results),
                "queries_per_second": concurrency / total_time
            }
        
        # Performance assertions
        for concurrency, metrics in results.items():
            assert metrics["avg_latency"] < 1000, f"Average latency too high at {concurrency} concurrent: {metrics['avg_latency']}ms"
            assert metrics["queries_per_second"] > concurrency * 0.5, f"Throughput too low at {concurrency} concurrent"
        
        # Scalability check - latency shouldn't degrade too much with concurrency
        base_latency = results[1]["avg_latency"]
        high_concurrency_latency = results[max(concurrent_levels)]["avg_latency"]
        latency_degradation = high_concurrency_latency / base_latency
        
        assert latency_degradation < 5, f"Latency degradation too high: {latency_degradation}x"
        
        print(f"\nConcurrency Performance Results:")
        for concurrency, metrics in results.items():
            print(f"{concurrency} concurrent:")
            print(f"  Avg latency: {metrics['avg_latency']:.2f}ms")
            print(f"  QPS: {metrics['queries_per_second']:.2f}")
            print(f"  Cache hit ratio: {metrics['cache_hit_ratio']:.2f}")
    
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self, performance_knowledge_base):
        """Test performance under sustained load"""
        kb = performance_knowledge_base
        
        duration_seconds = 30  # 30-second sustained load test
        target_qps = 10  # Target 10 queries per second
        
        query_count = 0
        latencies = []
        errors = 0
        cache_hits = 0
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        async def sustained_query_loop():
            nonlocal query_count, latencies, errors, cache_hits
            
            while time.time() < end_time:
                try:
                    query_start = time.time()
                    
                    params = QueryParams(
                        query=f"sustained load query {query_count % 20}",  # Cycle through 20 different queries
                        limit=5
                    )
                    
                    response = await kb.query(params)
                    
                    query_end = time.time()
                    latency = (query_end - query_start) * 1000
                    
                    latencies.append(latency)
                    query_count += 1
                    
                    if response.from_cache:
                        cache_hits += 1
                    
                    # Control rate to achieve target QPS
                    await asyncio.sleep(1.0 / target_qps)
                    
                except Exception as e:
                    errors += 1
                    print(f"Query error: {e}")
        
        # Run sustained load
        await sustained_query_loop()
        
        actual_duration = time.time() - start_time
        actual_qps = query_count / actual_duration
        avg_latency = statistics.mean(latencies) if latencies else 0
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies) if latencies else 0
        cache_hit_ratio = cache_hits / query_count if query_count > 0 else 0
        
        # Performance assertions
        assert errors == 0, f"Had {errors} errors during sustained load"
        assert avg_latency < 300, f"Average latency too high during sustained load: {avg_latency}ms"
        assert p95_latency < 800, f"P95 latency too high during sustained load: {p95_latency}ms"
        assert cache_hit_ratio > 0.6, f"Cache hit ratio too low during sustained load: {cache_hit_ratio}"
        assert actual_qps >= target_qps * 0.9, f"Actual QPS too low: {actual_qps} vs target {target_qps}"
        
        print(f"\nSustained Load Results ({duration_seconds}s):")
        print(f"  Queries executed: {query_count}")
        print(f"  Actual QPS: {actual_qps:.2f}")
        print(f"  Average latency: {avg_latency:.2f}ms")
        print(f"  P95 latency: {p95_latency:.2f}ms")
        print(f"  Cache hit ratio: {cache_hit_ratio:.2f}")
        print(f"  Errors: {errors}")


@pytest.mark.performance
class TestCachePerformance:
    """Test cache performance benchmarks"""
    
    @pytest.mark.asyncio
    async def test_memory_cache_performance(self):
        """Benchmark memory cache operations"""
        cache = MemoryCache(max_size_mb=50, default_ttl_seconds=3600)
        
        # Warm up
        for i in range(100):
            await cache.set(f"warmup_{i}", f"value_{i}")
        
        # Benchmark set operations
        set_times = []
        for i in range(1000):
            start_time = time.time()
            await cache.set(f"set_perf_{i}", f"performance_value_{i}")
            end_time = time.time()
            set_times.append((end_time - start_time) * 1000000)  # microseconds
        
        # Benchmark get operations
        get_times = []
        for i in range(1000):
            start_time = time.time()
            value = await cache.get(f"set_perf_{i}")
            end_time = time.time()
            get_times.append((end_time - start_time) * 1000000)  # microseconds
            assert value == f"performance_value_{i}"
        
        # Benchmark delete operations
        delete_times = []
        for i in range(500):
            start_time = time.time()
            await cache.delete(f"set_perf_{i}")
            end_time = time.time()
            delete_times.append((end_time - start_time) * 1000000)  # microseconds
        
        # Performance assertions (operations should be very fast)
        avg_set_time = statistics.mean(set_times)
        avg_get_time = statistics.mean(get_times)
        avg_delete_time = statistics.mean(delete_times)
        
        assert avg_set_time < 100, f"Memory cache set too slow: {avg_set_time}μs"  # < 100 microseconds
        assert avg_get_time < 50, f"Memory cache get too slow: {avg_get_time}μs"   # < 50 microseconds
        assert avg_delete_time < 100, f"Memory cache delete too slow: {avg_delete_time}μs"  # < 100 microseconds
        
        print(f"\nMemory Cache Performance:")
        print(f"  Average set time: {avg_set_time:.2f}μs")
        print(f"  Average get time: {avg_get_time:.2f}μs")
        print(f"  Average delete time: {avg_delete_time:.2f}μs")
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_manager_performance(self):
        """Benchmark cache manager operations"""
        cache_config = CacheConfig(memory_enabled=True, redis_enabled=False)
        memory_cache = MemoryCache(max_size_mb=20, default_ttl_seconds=3600)
        cache_manager = CacheManager(cache_config)
        await cache_manager.initialize(memory_cache, None)
        
        # Test query caching performance
        query_cache_times = []
        
        for i in range(500):
            query = f"performance test query {i}"
            result_data = [{"content": f"result {i}", "score": 0.9}]
            
            # Time cache set
            start_time = time.time()
            await cache_manager.set_query_cache(query, result_data, {"limit": 10})
            end_time = time.time()
            query_cache_times.append((end_time - start_time) * 1000)  # milliseconds
        
        # Test query cache retrieval
        query_get_times = []
        
        for i in range(500):
            query = f"performance test query {i}"
            
            start_time = time.time()
            cached_result = await cache_manager.get_query_cache(query, {"limit": 10})
            end_time = time.time()
            
            query_get_times.append((end_time - start_time) * 1000)  # milliseconds
            assert cached_result is not None
        
        avg_cache_set_time = statistics.mean(query_cache_times)
        avg_cache_get_time = statistics.mean(query_get_times)
        
        assert avg_cache_set_time < 10, f"Query cache set too slow: {avg_cache_set_time}ms"
        assert avg_cache_get_time < 5, f"Query cache get too slow: {avg_cache_get_time}ms"
        
        print(f"\nCache Manager Performance:")
        print(f"  Average query cache set: {avg_cache_set_time:.2f}ms")
        print(f"  Average query cache get: {avg_cache_get_time:.2f}ms")
        
        await cache_manager.close()
    
    @pytest.mark.asyncio
    async def test_cache_eviction_performance(self):
        """Test cache eviction performance under memory pressure"""
        # Create cache with limited memory to trigger evictions
        cache = MemoryCache(max_size_mb=5, default_ttl_seconds=3600)
        
        # Fill cache beyond capacity
        large_value = "x" * (1024 * 100)  # 100KB values
        
        eviction_times = []
        total_sets = 0
        
        for i in range(100):  # Try to add 10MB to 5MB cache
            start_time = time.time()
            await cache.set(f"eviction_test_{i}", large_value)
            end_time = time.time()
            
            set_time = (end_time - start_time) * 1000  # milliseconds
            eviction_times.append(set_time)
            total_sets += 1
            
            # Check if evictions occurred
            stats = await cache.get_stats()
            if stats["evictions"] > 0:
                break
        
        avg_eviction_time = statistics.mean(eviction_times)
        max_eviction_time = max(eviction_times)
        
        # Eviction should not significantly slow down operations
        assert avg_eviction_time < 50, f"Cache eviction too slow: {avg_eviction_time}ms"
        assert max_eviction_time < 200, f"Max eviction time too slow: {max_eviction_time}ms"
        
        final_stats = await cache.get_stats()
        assert final_stats["evictions"] > 0, "No evictions occurred during test"
        
        print(f"\nCache Eviction Performance:")
        print(f"  Average set time with eviction: {avg_eviction_time:.2f}ms")
        print(f"  Max set time: {max_eviction_time:.2f}ms")
        print(f"  Total evictions: {final_stats['evictions']}")
        
        await cache.close()


@pytest.mark.performance
class TestVectorStorePerformance:
    """Test vector store performance benchmarks"""
    
    @pytest.mark.asyncio
    async def test_chroma_client_performance(self):
        """Benchmark ChromaClient operations"""
        client = ChromaClient()
        client._collection = MagicMock()
        
        # Mock responses for performance testing
        client._collection.add.return_value = None
        client._collection.query.return_value = {
            "documents": [["doc1", "doc2", "doc3"]],
            "metadatas": [[{"title": "Title 1"}, {"title": "Title 2"}, {"title": "Title 3"}]],
            "distances": [[0.1, 0.2, 0.3]],
            "ids": [["id1", "id2", "id3"]]
        }
        
        # Test document addition performance
        documents = []
        for i in range(100):
            doc = ChromaDocument(
                id=f"perf_doc_{i}",
                content=f"Performance test document {i} with realistic content length that would be typical in a production system",
                metadata={
                    "title": f"Document {i}",
                    "category": f"category_{i % 10}",
                    "timestamp": time.time(),
                    "author": f"author_{i % 5}"
                }
            )
            documents.append(doc)
        
        # Benchmark batch document addition
        start_time = time.time()
        await client.add_documents(documents, batch_size=32)
        end_time = time.time()
        
        add_time = (end_time - start_time) * 1000  # milliseconds
        docs_per_second = len(documents) / (add_time / 1000)
        
        assert add_time < 5000, f"Document addition too slow: {add_time}ms for {len(documents)} docs"
        assert docs_per_second > 20, f"Document addition rate too low: {docs_per_second} docs/second"
        
        # Benchmark search operations
        search_times = []
        
        for i in range(50):
            start_time = time.time()
            results = await client.search(
                query=f"performance test query {i}",
                limit=10,
                score_threshold=0.3
            )
            end_time = time.time()
            
            search_time = (end_time - start_time) * 1000  # milliseconds
            search_times.append(search_time)
        
        avg_search_time = statistics.mean(search_times)
        p95_search_time = statistics.quantiles(search_times, n=20)[18] if len(search_times) >= 20 else max(search_times)
        
        assert avg_search_time < 100, f"Search too slow: {avg_search_time}ms average"
        assert p95_search_time < 200, f"Search P95 too slow: {p95_search_time}ms"
        
        print(f"\nVector Store Performance:")
        print(f"  Document addition: {docs_per_second:.2f} docs/second")
        print(f"  Average search time: {avg_search_time:.2f}ms")
        print(f"  P95 search time: {p95_search_time:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_search_result_processing_performance(self):
        """Benchmark search result processing"""
        client = ChromaClient()
        
        # Create large result set for processing
        num_results = 10000
        raw_results = {
            "documents": [[f"Document {i} with substantial content that would be typical in a real knowledge base system" for i in range(num_results)]],
            "metadatas": [[{"title": f"Title {i}", "category": f"cat_{i % 100}", "score": i / num_results} for i in range(num_results)]],
            "distances": [[i / num_results for i in range(num_results)]],
            "ids": [[f"id_{i}" for i in range(num_results)]]
        }
        
        # Benchmark result processing
        start_time = time.time()
        processed_results = client._process_search_results(raw_results, 0.1)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000  # milliseconds
        results_per_second = len(processed_results) / (processing_time / 1000)
        
        assert processing_time < 1000, f"Result processing too slow: {processing_time}ms for {num_results} results"
        assert results_per_second > 1000, f"Result processing rate too low: {results_per_second} results/second"
        assert len(processed_results) > 0, "No results processed"
        
        print(f"\nResult Processing Performance:")
        print(f"  Processing time: {processing_time:.2f}ms for {num_results} results")
        print(f"  Processing rate: {results_per_second:.0f} results/second")
        print(f"  Results after filtering: {len(processed_results)}")


@pytest.mark.performance
class TestMemoryUsagePerformance:
    """Test memory usage and efficiency"""
    
    @pytest.mark.asyncio
    async def test_memory_cache_efficiency(self):
        """Test memory cache memory usage efficiency"""
        cache = MemoryCache(max_size_mb=10, default_ttl_seconds=3600)
        
        # Add predictable amount of data
        num_entries = 1000
        value_size = 1024  # 1KB per entry = 1MB total
        test_value = "x" * value_size
        
        for i in range(num_entries):
            await cache.set(f"memory_test_{i}", test_value)
        
        stats = await cache.get_stats()
        
        # Check memory estimation accuracy
        estimated_mb = stats["estimated_size_mb"]
        expected_mb = (num_entries * value_size) / (1024 * 1024)
        
        # Memory estimation should be reasonably accurate (within 50% variance)
        estimation_ratio = estimated_mb / expected_mb
        assert 0.5 <= estimation_ratio <= 2.0, f"Memory estimation inaccurate: {estimated_mb}MB vs expected {expected_mb}MB"
        
        # Should stay within configured limits
        assert estimated_mb <= cache.max_size_mb * 1.2, f"Memory usage exceeded limits: {estimated_mb}MB > {cache.max_size_mb}MB"
        
        print(f"\nMemory Efficiency:")
        print(f"  Entries: {stats['entries_count']}")
        print(f"  Estimated size: {estimated_mb:.2f}MB")
        print(f"  Expected size: {expected_mb:.2f}MB")
        print(f"  Estimation accuracy: {estimation_ratio:.2f}x")
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_memory_growth_patterns(self):
        """Test memory growth patterns under different workloads"""
        cache = MemoryCache(max_size_mb=20, default_ttl_seconds=3600)
        
        memory_samples = []
        
        # Phase 1: Linear growth
        for i in range(500):
            await cache.set(f"growth_test_{i}", f"value_{i}")
            
            if i % 50 == 0:
                stats = await cache.get_stats()
                memory_samples.append({
                    "phase": "linear_growth",
                    "entries": stats["entries_count"],
                    "memory_mb": stats["estimated_size_mb"],
                    "step": i
                })
        
        # Phase 2: High churn (add and delete)
        for i in range(500, 1000):
            await cache.set(f"churn_test_{i}", f"value_{i}")
            if i > 600:
                await cache.delete(f"churn_test_{i - 100}")
            
            if i % 50 == 0:
                stats = await cache.get_stats()
                memory_samples.append({
                    "phase": "high_churn",
                    "entries": stats["entries_count"],
                    "memory_mb": stats["estimated_size_mb"],
                    "step": i
                })
        
        # Phase 3: Memory pressure (large values)
        large_value = "x" * (1024 * 50)  # 50KB values
        for i in range(100):
            await cache.set(f"pressure_test_{i}", large_value)
            
            if i % 10 == 0:
                stats = await cache.get_stats()
                memory_samples.append({
                    "phase": "memory_pressure",
                    "entries": stats["entries_count"],
                    "memory_mb": stats["estimated_size_mb"],
                    "evictions": stats["evictions"],
                    "step": i
                })
        
        # Analyze memory growth patterns
        final_stats = await cache.get_stats()
        
        # Should have triggered evictions during pressure phase
        assert final_stats["evictions"] > 0, "No evictions occurred during memory pressure"
        
        # Memory should be managed within limits
        assert final_stats["estimated_size_mb"] <= cache.max_size_mb * 1.5, "Memory not properly managed"
        
        print(f"\nMemory Growth Analysis:")
        print(f"  Final entries: {final_stats['entries_count']}")
        print(f"  Final memory: {final_stats['estimated_size_mb']:.2f}MB")
        print(f"  Total evictions: {final_stats['evictions']}")
        
        for sample in memory_samples[-3:]:  # Show last 3 samples
            print(f"  {sample['phase']}: {sample['entries']} entries, {sample['memory_mb']:.2f}MB")
        
        await cache.close()


@pytest.mark.performance
@pytest.mark.slow
class TestStressTestPerformance:
    """Stress tests for extreme performance scenarios"""
    
    @pytest.mark.asyncio
    async def test_extreme_concurrent_load(self, performance_knowledge_base):
        """Test performance under extreme concurrent load"""
        kb = performance_knowledge_base
        
        # Extreme concurrency levels
        max_concurrency = 100
        queries_per_worker = 10
        
        async def stress_worker(worker_id):
            worker_times = []
            worker_errors = 0
            
            for i in range(queries_per_worker):
                try:
                    start_time = time.time()
                    
                    params = QueryParams(
                        query=f"stress test {worker_id} query {i}",
                        limit=5
                    )
                    
                    response = await kb.query(params)
                    
                    end_time = time.time()
                    worker_times.append((end_time - start_time) * 1000)
                    
                    # Small delay to avoid overwhelming
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    worker_errors += 1
                    print(f"Worker {worker_id} error: {e}")
            
            return {
                "worker_id": worker_id,
                "times": worker_times,
                "errors": worker_errors,
                "avg_time": statistics.mean(worker_times) if worker_times else 0
            }
        
        # Execute stress test
        start_time = time.time()
        
        tasks = [stress_worker(i) for i in range(max_concurrency)]
        worker_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful_workers = [r for r in worker_results if not isinstance(r, Exception)]
        failed_workers = [r for r in worker_results if isinstance(r, Exception)]
        
        total_queries = sum(len(w["times"]) for w in successful_workers)
        total_errors = sum(w["errors"] for w in successful_workers)
        all_times = []
        for w in successful_workers:
            all_times.extend(w["times"])
        
        # Performance assertions
        success_rate = len(successful_workers) / len(worker_results)
        error_rate = total_errors / total_queries if total_queries > 0 else 1
        avg_latency = statistics.mean(all_times) if all_times else float('inf')
        queries_per_second = total_queries / total_duration
        
        assert success_rate > 0.95, f"Too many worker failures: {success_rate:.2%} success rate"
        assert error_rate < 0.05, f"Too many query errors: {error_rate:.2%} error rate"
        assert avg_latency < 2000, f"Latency too high under stress: {avg_latency:.2f}ms"
        assert queries_per_second > max_concurrency * 0.5, f"Throughput too low: {queries_per_second:.2f} QPS"
        
        print(f"\nExtreme Concurrent Load Results:")
        print(f"  Workers: {max_concurrency}")
        print(f"  Total queries: {total_queries}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Error rate: {error_rate:.2%}")
        print(f"  Average latency: {avg_latency:.2f}ms")
        print(f"  Queries per second: {queries_per_second:.2f}")
        print(f"  Failed workers: {len(failed_workers)}")
    
    @pytest.mark.asyncio
    async def test_long_running_stability(self, performance_knowledge_base):
        """Test long-running stability and performance degradation"""
        kb = performance_knowledge_base
        
        duration_minutes = 5  # 5-minute stability test
        target_qps = 5
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        query_count = 0
        error_count = 0
        latency_samples = []
        memory_samples = []
        
        # Sample metrics every 30 seconds
        last_sample_time = start_time
        
        while time.time() < end_time:
            try:
                query_start = time.time()
                
                params = QueryParams(
                    query=f"long running test {query_count % 100}",
                    limit=10
                )
                
                response = await kb.query(params)
                
                query_end = time.time()
                latency = (query_end - query_start) * 1000
                latency_samples.append(latency)
                query_count += 1
                
                # Sample metrics periodically
                if query_end - last_sample_time >= 30:  # Every 30 seconds
                    stats = await kb.get_stats()
                    
                    cache_stats = stats.get("cache", {}).get("manager", {})
                    memory_samples.append({
                        "timestamp": query_end - start_time,
                        "total_queries": stats["knowledge_base"]["total_queries"],
                        "cache_hit_ratio": cache_stats.get("overall_hit_ratio", 0),
                        "avg_query_time": stats["knowledge_base"]["avg_query_time_ms"]
                    })
                    
                    last_sample_time = query_end
                
                # Control rate
                await asyncio.sleep(1.0 / target_qps)
                
            except Exception as e:
                error_count += 1
                print(f"Long-running test error: {e}")
        
        actual_duration = time.time() - start_time
        
        # Analyze stability
        if latency_samples:
            # Check for performance degradation over time
            early_samples = latency_samples[:len(latency_samples)//4]  # First 25%
            late_samples = latency_samples[-len(latency_samples)//4:]  # Last 25%
            
            early_avg = statistics.mean(early_samples)
            late_avg = statistics.mean(late_samples)
            degradation_ratio = late_avg / early_avg if early_avg > 0 else 1
            
            overall_avg = statistics.mean(latency_samples)
            overall_p95 = statistics.quantiles(latency_samples, n=20)[18] if len(latency_samples) >= 20 else max(latency_samples)
        else:
            early_avg = late_avg = overall_avg = overall_p95 = 0
            degradation_ratio = 1
        
        # Stability assertions
        error_rate = error_count / query_count if query_count > 0 else 1
        actual_qps = query_count / actual_duration
        
        assert error_rate < 0.01, f"Too many errors in long run: {error_rate:.2%}"
        assert degradation_ratio < 2, f"Performance degraded too much: {degradation_ratio:.2f}x"
        assert overall_avg < 500, f"Average latency too high: {overall_avg:.2f}ms"
        assert overall_p95 < 1000, f"P95 latency too high: {overall_p95:.2f}ms"
        
        print(f"\nLong-Running Stability Results ({duration_minutes} minutes):")
        print(f"  Total queries: {query_count}")
        print(f"  Actual QPS: {actual_qps:.2f}")
        print(f"  Error rate: {error_rate:.2%}")
        print(f"  Early avg latency: {early_avg:.2f}ms")
        print(f"  Late avg latency: {late_avg:.2f}ms")
        print(f"  Performance degradation: {degradation_ratio:.2f}x")
        print(f"  Overall P95 latency: {overall_p95:.2f}ms")
        
        if memory_samples:
            print(f"  Samples collected: {len(memory_samples)}")
            for sample in memory_samples[::2]:  # Every other sample
                print(f"    {sample['timestamp']/60:.1f}min: {sample['total_queries']} queries, "
                      f"{sample['cache_hit_ratio']:.2f} hit ratio, {sample['avg_query_time']:.2f}ms avg")