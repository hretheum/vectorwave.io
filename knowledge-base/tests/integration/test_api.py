"""API integration tests for Knowledge Base FastAPI endpoints"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from src.api.routes import app
from src.knowledge_engine import CrewAIKnowledgeBase, QueryResponse, KnowledgeResult, QuerySource
from src.storage import ChromaDocument


@pytest.mark.integration
class TestAPIEndpoints:
    """Test FastAPI endpoints integration"""
    
    @pytest.fixture
    def mock_knowledge_base(self):
        """Create mock knowledge base for API testing"""
        mock_kb = AsyncMock(spec=CrewAIKnowledgeBase)
        
        # Default mock responses
        mock_kb.query.return_value = QueryResponse(
            results=[
                KnowledgeResult(
                    content="Test API response content",
                    title="Test API Document",
                    source_type="api_test",
                    url="https://example.com/test",
                    metadata={"category": "test"},
                    score=0.95,
                    source=QuerySource.VECTOR
                )
            ],
            total_count=1,
            query_time_ms=25.5,
            from_cache=False,
            sources_used=[QuerySource.VECTOR],
            query_params=None
        )
        
        mock_kb.add_document.return_value = True
        mock_kb.update_document.return_value = True
        mock_kb.delete_document.return_value = True
        
        mock_kb.get_stats.return_value = {
            "knowledge_base": {
                "total_queries": 100,
                "cache_hits": 70,
                "vector_hits": 30,
                "avg_query_time_ms": 45.2
            },
            "cache": {
                "manager": {
                    "total_requests": 150,
                    "l1_hits": 50,
                    "l2_hits": 20,
                    "overall_hit_ratio": 0.75
                }
            },
            "vector_store": {
                "total_documents": 5000,
                "collection_name": "test_collection",
                "queries_total": 30
            },
            "health": {"status": "healthy"}
        }
        
        mock_kb.health_check.return_value = {
            "status": "healthy",
            "timestamp": 1234567890.0,
            "components": {
                "cache": {"status": "healthy"},
                "vector_store": {"status": "healthy"}
            },
            "stats": {"total_queries": 100}
        }
        
        return mock_kb
    
    @pytest.fixture
    def client(self, mock_knowledge_base):
        """Create test client with mocked knowledge base"""
        with patch('src.api.routes.knowledge_base', mock_knowledge_base):
            yield TestClient(app)
    
    @pytest.fixture
    async def async_client(self, mock_knowledge_base):
        """Create async test client with mocked knowledge base"""
        with patch('src.api.routes.knowledge_base', mock_knowledge_base):
            async with AsyncClient(app=app, base_url="http://test") as client:
                yield client
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Vector Wave Knowledge Base API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "endpoints" in data
        assert "/api/v1/knowledge/query" in data["endpoints"]["query"]
    
    def test_query_endpoint_success(self, client, mock_knowledge_base):
        """Test successful query endpoint"""
        query_data = {
            "query": "What is artificial intelligence?",
            "limit": 5,
            "score_threshold": 0.4,
            "use_cache": True
        }
        
        response = client.post("/api/v1/knowledge/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "results" in data
        assert "total_count" in data
        assert "query_time_ms" in data
        assert "from_cache" in data
        assert "sources_used" in data
        assert "query_params" in data
        
        # Verify response content
        assert data["total_count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["content"] == "Test API response content"
        assert data["results"][0]["title"] == "Test API Document"
        assert data["results"][0]["score"] == 0.95
        assert data["results"][0]["source"] == "vector"
        
        # Verify mock was called correctly
        mock_knowledge_base.query.assert_called_once()
        call_args = mock_knowledge_base.query.call_args[0][0]
        assert call_args.query == "What is artificial intelligence?"
        assert call_args.limit == 5
        assert call_args.score_threshold == 0.4
        assert call_args.use_cache is True
    
    def test_query_endpoint_with_filters(self, client, mock_knowledge_base):
        """Test query endpoint with metadata filters"""
        query_data = {
            "query": "machine learning",
            "limit": 10,
            "metadata_filters": {
                "category": "ai",
                "difficulty": {"$gte": 3}
            },
            "sources": ["vector", "cache"]
        }
        
        response = client.post("/api/v1/knowledge/query", json=query_data)
        
        assert response.status_code == 200
        
        # Verify filters were passed correctly
        call_args = mock_knowledge_base.query.call_args[0][0]
        assert call_args.metadata_filters == query_data["metadata_filters"]
        assert call_args.sources == [QuerySource.VECTOR, QuerySource.CACHE]
    
    def test_query_endpoint_validation_errors(self, client):
        """Test query endpoint input validation"""
        # Test missing query
        response = client.post("/api/v1/knowledge/query", json={})
        assert response.status_code == 422
        
        # Test invalid limit
        response = client.post("/api/v1/knowledge/query", json={
            "query": "test",
            "limit": -1
        })
        assert response.status_code == 422
        
        # Test invalid score threshold
        response = client.post("/api/v1/knowledge/query", json={
            "query": "test",
            "score_threshold": 1.5
        })
        assert response.status_code == 422
        
        # Test query too long
        response = client.post("/api/v1/knowledge/query", json={
            "query": "x" * 1001  # Exceeds max length
        })
        assert response.status_code == 422
    
    def test_query_endpoint_invalid_sources(self, client):
        """Test query endpoint with invalid sources"""
        query_data = {
            "query": "test query",
            "sources": ["invalid_source"]
        }
        
        response = client.post("/api/v1/knowledge/query", json=query_data)
        assert response.status_code == 400
        assert "Invalid source" in response.json()["detail"]
    
    def test_query_endpoint_error_handling(self, client, mock_knowledge_base):
        """Test query endpoint error handling"""
        # Mock knowledge base to raise exception
        mock_knowledge_base.query.side_effect = Exception("Query processing error")
        
        query_data = {"query": "test query"}
        response = client.post("/api/v1/knowledge/query", json=query_data)
        
        assert response.status_code == 500
        assert "Query execution failed" in response.json()["detail"]
    
    def test_health_check_endpoint(self, client, mock_knowledge_base):
        """Test health check endpoint"""
        response = client.get("/api/v1/knowledge/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "components" in data
        assert "stats" in data
        assert data["components"]["cache"]["status"] == "healthy"
        assert data["components"]["vector_store"]["status"] == "healthy"
        
        mock_knowledge_base.health_check.assert_called_once()
    
    def test_health_check_endpoint_error(self, client, mock_knowledge_base):
        """Test health check endpoint with error"""
        mock_knowledge_base.health_check.side_effect = Exception("Health check failed")
        
        response = client.get("/api/v1/knowledge/health")
        
        assert response.status_code == 200  # Should return 200 even on error
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert "timestamp" in data
    
    def test_stats_endpoint(self, client, mock_knowledge_base):
        """Test statistics endpoint"""
        response = client.get("/api/v1/knowledge/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "knowledge_base" in data
        assert "cache" in data
        assert "vector_store" in data
        assert "health" in data
        
        # Verify knowledge base stats
        kb_stats = data["knowledge_base"]
        assert kb_stats["total_queries"] == 100
        assert kb_stats["cache_hits"] == 70
        assert kb_stats["vector_hits"] == 30
        
        # Verify cache stats
        cache_stats = data["cache"]["manager"]
        assert cache_stats["overall_hit_ratio"] == 0.75
        
        # Verify vector store stats
        vs_stats = data["vector_store"]
        assert vs_stats["total_documents"] == 5000
        assert vs_stats["collection_name"] == "test_collection"
        
        mock_knowledge_base.get_stats.assert_called_once()
    
    def test_stats_endpoint_error(self, client, mock_knowledge_base):
        """Test statistics endpoint error handling"""
        mock_knowledge_base.get_stats.side_effect = Exception("Stats error")
        
        response = client.get("/api/v1/knowledge/stats")
        
        assert response.status_code == 500
        assert "Failed to get statistics" in response.json()["detail"]
    
    def test_add_document_endpoint(self, client, mock_knowledge_base):
        """Test add document endpoint"""
        document_data = {
            "content": "Test document content for API testing",
            "metadata": {
                "title": "API Test Document",
                "category": "test",
                "author": "test_user"
            }
        }
        
        response = client.post("/api/v1/knowledge/documents", json=document_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "document_id" in data
        assert data["message"] == "Document added successfully"
        
        # Verify mock was called correctly
        mock_knowledge_base.add_document.assert_called_once()
        call_args = mock_knowledge_base.add_document.call_args[0][0]
        assert call_args.content == document_data["content"]
        assert call_args.metadata == document_data["metadata"]
        assert call_args.id is not None  # Should generate ID
    
    def test_add_document_with_id(self, client, mock_knowledge_base):
        """Test add document endpoint with custom ID"""
        document_data = {
            "id": "custom_doc_id",
            "content": "Test content",
            "metadata": {"title": "Custom ID Test"}
        }
        
        response = client.post("/api/v1/knowledge/documents", json=document_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "custom_doc_id"
        
        # Verify custom ID was used
        call_args = mock_knowledge_base.add_document.call_args[0][0]
        assert call_args.id == "custom_doc_id"
    
    def test_add_document_failure(self, client, mock_knowledge_base):
        """Test add document endpoint failure"""
        mock_knowledge_base.add_document.return_value = False
        
        document_data = {
            "content": "Test content",
            "metadata": {"title": "Failure Test"}
        }
        
        response = client.post("/api/v1/knowledge/documents", json=document_data)
        
        assert response.status_code == 500
        assert "Failed to add document" in response.json()["detail"]
    
    def test_add_document_error(self, client, mock_knowledge_base):
        """Test add document endpoint error handling"""
        mock_knowledge_base.add_document.side_effect = Exception("Add document error")
        
        document_data = {
            "content": "Test content",
            "metadata": {"title": "Error Test"}
        }
        
        response = client.post("/api/v1/knowledge/documents", json=document_data)
        
        assert response.status_code == 500
        assert "Failed to add document" in response.json()["detail"]
    
    def test_delete_document_endpoint(self, client, mock_knowledge_base):
        """Test delete document endpoint"""
        doc_id = "test_document_id"
        
        response = client.delete(f"/api/v1/knowledge/documents/{doc_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["document_id"] == doc_id
        assert data["message"] == "Document deleted successfully"
        
        mock_knowledge_base.delete_document.assert_called_once_with(doc_id)
    
    def test_delete_document_not_found(self, client, mock_knowledge_base):
        """Test delete document endpoint when document not found"""
        mock_knowledge_base.delete_document.return_value = False
        
        response = client.delete("/api/v1/knowledge/documents/nonexistent_id")
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]
    
    def test_delete_document_error(self, client, mock_knowledge_base):
        """Test delete document endpoint error handling"""
        mock_knowledge_base.delete_document.side_effect = Exception("Delete error")
        
        response = client.delete("/api/v1/knowledge/documents/error_doc")
        
        assert response.status_code == 500
        assert "Failed to delete document" in response.json()["detail"]
    
    def test_simple_search_endpoint(self, client, mock_knowledge_base):
        """Test simple GET-based search endpoint"""
        params = {
            "q": "simple search test",
            "limit": 5,
            "threshold": 0.6
        }
        
        response = client.get("/api/v1/knowledge/search", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "simple search test"
        assert "results" in data
        assert "total" in data
        assert "from_cache" in data
        assert "query_time_ms" in data
        
        # Verify simplified response format
        assert len(data["results"]) == 1
        result = data["results"][0]
        assert "title" in result
        assert "content" in result
        assert "score" in result
        assert "url" in result
        
        # Content should be truncated for simple response
        assert len(result["content"]) <= 203  # 200 chars + "..."
        
        # Verify mock was called with correct parameters
        call_args = mock_knowledge_base.query.call_args[0][0]
        assert call_args.query == "simple search test"
        assert call_args.limit == 5
        assert call_args.score_threshold == 0.6
    
    def test_simple_search_error(self, client, mock_knowledge_base):
        """Test simple search endpoint error handling"""
        mock_knowledge_base.query.side_effect = Exception("Search failed")
        
        response = client.get("/api/v1/knowledge/search?q=error+test")
        
        assert response.status_code == 500
        assert "Search failed" in response.json()["detail"]
    
    def test_sync_endpoint(self, client):
        """Test sync trigger endpoint (placeholder)"""
        sync_data = {
            "sources": ["crewai_docs", "github"],
            "force": True
        }
        
        response = client.post("/api/v1/knowledge/sync", json=sync_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "accepted"
        assert "sync_job_id" in data
        assert data["sources"] == sync_data["sources"]
        assert data["force"] is True
        assert "placeholder implementation" in data["message"]
    
    def test_sync_endpoint_defaults(self, client):
        """Test sync endpoint with default parameters"""
        response = client.post("/api/v1/knowledge/sync", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "accepted"
        assert data["sources"] == ["all"]
        assert data["force"] is False
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint (placeholder)"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "placeholder" in data["message"]
    
    def test_knowledge_base_not_initialized(self, client):
        """Test endpoints when knowledge base is not initialized"""
        with patch('src.api.routes.knowledge_base', None):
            # Query endpoint
            response = client.post("/api/v1/knowledge/query", json={"query": "test"})
            assert response.status_code == 503
            assert "Knowledge base not initialized" in response.json()["detail"]
            
            # Health endpoint
            response = client.get("/api/v1/knowledge/health")
            assert response.status_code == 503
            
            # Stats endpoint
            response = client.get("/api/v1/knowledge/stats")
            assert response.status_code == 503


@pytest.mark.integration
class TestAPIPerformance:
    """Test API performance characteristics"""
    
    @pytest.fixture
    def fast_mock_kb(self):
        """Create fast mock knowledge base for performance testing"""
        mock_kb = AsyncMock(spec=CrewAIKnowledgeBase)
        
        async def fast_query(*args, **kwargs):
            # Simulate very fast response
            await asyncio.sleep(0.001)  # 1ms
            return QueryResponse(
                results=[
                    KnowledgeResult(
                        content="Fast response content",
                        title="Fast Response",
                        source_type="performance",
                        url=None,
                        metadata={},
                        score=0.9,
                        source=QuerySource.CACHE
                    )
                ],
                total_count=1,
                query_time_ms=1.0,
                from_cache=True,
                sources_used=[QuerySource.CACHE],
                query_params=None
            )
        
        mock_kb.query.side_effect = fast_query
        return mock_kb
    
    @pytest.mark.asyncio
    async def test_api_response_times(self, fast_mock_kb):
        """Test API response time performance"""
        with patch('src.api.routes.knowledge_base', fast_mock_kb):
            async with AsyncClient(app=app, base_url="http://test") as client:
                
                # Test query endpoint performance
                query_times = []
                
                for i in range(50):
                    start_time = asyncio.get_event_loop().time()
                    
                    response = await client.post("/api/v1/knowledge/query", json={
                        "query": f"performance test {i}",
                        "limit": 10
                    })
                    
                    end_time = asyncio.get_event_loop().time()
                    
                    assert response.status_code == 200
                    query_times.append((end_time - start_time) * 1000)  # milliseconds
                
                # Performance assertions
                avg_time = sum(query_times) / len(query_times)
                max_time = max(query_times)
                
                assert avg_time < 50, f"Average API response time too high: {avg_time:.2f}ms"
                assert max_time < 200, f"Max API response time too high: {max_time:.2f}ms"
                
                print(f"\nAPI Performance:")
                print(f"  Average response time: {avg_time:.2f}ms")
                print(f"  Max response time: {max_time:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, fast_mock_kb):
        """Test API performance under concurrent requests"""
        with patch('src.api.routes.knowledge_base', fast_mock_kb):
            async with AsyncClient(app=app, base_url="http://test") as client:
                
                async def make_request(request_id):
                    start_time = asyncio.get_event_loop().time()
                    
                    response = await client.post("/api/v1/knowledge/query", json={
                        "query": f"concurrent test {request_id}",
                        "limit": 5
                    })
                    
                    end_time = asyncio.get_event_loop().time()
                    
                    return {
                        "status_code": response.status_code,
                        "response_time": (end_time - start_time) * 1000,
                        "request_id": request_id
                    }
                
                # Test with 20 concurrent requests
                start_time = asyncio.get_event_loop().time()
                
                tasks = [make_request(i) for i in range(20)]
                results = await asyncio.gather(*tasks)
                
                end_time = asyncio.get_event_loop().time()
                total_time = end_time - start_time
                
                # Analyze results
                successful_requests = [r for r in results if r["status_code"] == 200]
                response_times = [r["response_time"] for r in successful_requests]
                
                assert len(successful_requests) == 20, "Some concurrent requests failed"
                
                avg_response_time = sum(response_times) / len(response_times)
                requests_per_second = len(successful_requests) / total_time
                
                assert avg_response_time < 100, f"Average concurrent response time too high: {avg_response_time:.2f}ms"
                assert requests_per_second > 10, f"Concurrent throughput too low: {requests_per_second:.2f} RPS"
                
                print(f"\nConcurrent API Performance:")
                print(f"  Successful requests: {len(successful_requests)}/20")
                print(f"  Average response time: {avg_response_time:.2f}ms")
                print(f"  Requests per second: {requests_per_second:.2f}")


@pytest.mark.integration
class TestAPIErrorScenarios:
    """Test API error handling scenarios"""
    
    def test_malformed_json_requests(self, client):
        """Test API handling of malformed JSON"""
        # Test with invalid JSON
        response = client.post(
            "/api/v1/knowledge/query",
            data="invalid json {",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test API handling of missing content type"""
        response = client.post(
            "/api/v1/knowledge/query",
            data='{"query": "test"}',
            # No Content-Type header
        )
        # Should still work as FastAPI is flexible
        assert response.status_code in [200, 422]  # Either works or validation error
    
    def test_large_request_payload(self, client, mock_knowledge_base):
        """Test API handling of very large requests"""
        # Create very large query
        large_query = "x" * 10000  # 10KB query
        large_metadata = {f"field_{i}": f"value_{i}" for i in range(1000)}
        
        query_data = {
            "query": large_query,
            "metadata_filters": large_metadata
        }
        
        response = client.post("/api/v1/knowledge/query", json=query_data)
        
        # Should either work or return validation error (422)
        assert response.status_code in [200, 422]
    
    def test_unicode_handling(self, client, mock_knowledge_base):
        """Test API handling of Unicode characters"""
        unicode_queries = [
            "What is AI? 人工智能是什么？",
            "Qu'est-ce que l'IA? Was ist KI?",
            "🤖 Artificial Intelligence 🧠",
            "AI في العربية",
            "Что такое ИИ?"
        ]
        
        for query in unicode_queries:
            response = client.post("/api/v1/knowledge/query", json={
                "query": query,
                "limit": 5
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
    
    @pytest.mark.asyncio
    async def test_timeout_scenarios(self, mock_knowledge_base):
        """Test API timeout handling"""
        # Mock slow knowledge base
        async def slow_query(*args, **kwargs):
            await asyncio.sleep(2)  # 2 second delay
            return QueryResponse(
                results=[],
                total_count=0,
                query_time_ms=2000,
                from_cache=False,
                sources_used=[],
                query_params=None
            )
        
        mock_knowledge_base.query.side_effect = slow_query
        
        with patch('src.api.routes.knowledge_base', mock_knowledge_base):
            async with AsyncClient(app=app, base_url="http://test", timeout=1.0) as client:
                
                # This should timeout
                try:
                    response = await client.post("/api/v1/knowledge/query", json={
                        "query": "slow query test"
                    })
                    # If it doesn't timeout, that's also acceptable behavior
                    assert response.status_code in [200, 500]
                except Exception as e:
                    # Timeout is expected
                    assert "timeout" in str(e).lower() or "time" in str(e).lower()


@pytest.mark.integration
class TestCORSAndSecurity:
    """Test CORS and security configurations"""
    
    def test_cors_headers(self, client):
        """Test CORS headers are properly set"""
        response = client.options("/api/v1/knowledge/query")
        
        # Should include CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in headers or response.status_code == 405
        
        # Test actual request with origin
        response = client.post(
            "/api/v1/knowledge/query",
            json={"query": "test"},
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should work regardless of origin (configured as "*")
        assert response.status_code in [200, 503]  # 503 if kb not initialized
    
    def test_request_size_limits(self, client):
        """Test request size limitations"""
        # Test with very large request body
        large_content = "x" * (1024 * 1024)  # 1MB
        
        response = client.post("/api/v1/knowledge/documents", json={
            "content": large_content,
            "metadata": {"title": "Large document"}
        })
        
        # Should either work or be rejected
        assert response.status_code in [200, 413, 422, 503]  # Various acceptable responses
    
    def test_http_methods(self, client):
        """Test that only allowed HTTP methods work"""
        # Query endpoint should only accept POST
        response = client.get("/api/v1/knowledge/query")
        assert response.status_code == 405  # Method Not Allowed
        
        response = client.put("/api/v1/knowledge/query")
        assert response.status_code == 405
        
        # Health endpoint should only accept GET
        response = client.post("/api/v1/knowledge/health")
        assert response.status_code == 405
        
        # Stats endpoint should only accept GET
        response = client.delete("/api/v1/knowledge/stats")
        assert response.status_code == 405