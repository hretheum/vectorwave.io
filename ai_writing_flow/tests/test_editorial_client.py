"""
Tests for Editorial Service HTTP Client
Verifies client functionality and integration with Editorial Service
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from datetime import datetime

from ai_writing_flow.clients.editorial_client import (
    EditorialServiceClient,
    create_editorial_client
)


class TestEditorialServiceClient:
    """Test suite for Editorial Service Client"""
    
    @pytest.fixture
    async def client(self):
        """Create test client"""
        client = EditorialServiceClient(base_url="http://localhost:8040")
        yield client
        await client.close()
    
    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response"""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"status": "success"}
        response.raise_for_status = MagicMock()
        return response
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization with custom parameters"""
        client = EditorialServiceClient(
            base_url="http://custom:9000",
            timeout=60.0
        )
        
        assert client.base_url == "http://custom:9000"
        assert client.timeout == 60.0
        assert client._failure_threshold == 5
        assert client._recovery_timeout == 60
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality"""
        async with EditorialServiceClient() as client:
            assert isinstance(client, EditorialServiceClient)
            assert client.client is not None
    
    @pytest.mark.asyncio
    async def test_health_check(self, client, mock_response):
        """Test health check endpoint"""
        mock_response.json.return_value = {
            "status": "healthy",
            "service": "editorial-service",
            "version": "2.0.0"
        }
        
        with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
            result = await client.health_check()
            
            assert result["status"] == "healthy"
            assert result["service"] == "editorial-service"
            mock_get.assert_called_once_with("http://localhost:8040/health")
    
    @pytest.mark.asyncio
    async def test_validate_selective(self, client, mock_response):
        """Test selective validation for human-assisted workflow"""
        mock_response.json.return_value = {
            "validation_id": "val_123",
            "mode": "selective",
            "rules_applied": 3,
            "violations": [],
            "suggestions": ["Consider adding more context"]
        }
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.validate_selective(
                content="Test content",
                platform="linkedin",
                checkpoint="style",
                context={"user_id": "user_123"}
            )
            
            assert result["mode"] == "selective"
            assert result["rules_applied"] == 3
            assert len(result["suggestions"]) == 1
            
            # Verify request payload
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://localhost:8040/validate/selective"
            payload = call_args[1]["json"]
            assert payload["content"] == "Test content"
            assert payload["platform"] == "linkedin"
            assert payload["context"]["checkpoint"] == "style"
            assert payload["context"]["user_id"] == "user_123"
    
    @pytest.mark.asyncio
    async def test_validate_comprehensive(self, client, mock_response):
        """Test comprehensive validation for AI-first workflow"""
        mock_response.json.return_value = {
            "validation_id": "val_456",
            "mode": "comprehensive",
            "rules_applied": 10,
            "violations": [
                {"rule": "word_count", "severity": "warning"}
            ],
            "suggestions": []
        }
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.validate_comprehensive(
                content="Test article content",
                platform="twitter",
                content_type="thread",
                context={"topic": "AI"}
            )
            
            assert result["mode"] == "comprehensive"
            assert result["rules_applied"] == 10
            assert len(result["violations"]) == 1
            
            # Verify request payload
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://localhost:8040/validate/comprehensive"
            payload = call_args[1]["json"]
            assert payload["content"] == "Test article content"
            assert payload["platform"] == "twitter"
            assert payload["content_type"] == "thread"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, client):
        """Test circuit breaker functionality"""
        # Simulate failures
        error_response = MagicMock()
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=None, response=None
        )
        
        with patch.object(client.client, 'get', return_value=error_response):
            # Trigger failures up to threshold
            for i in range(5):
                with pytest.raises(httpx.HTTPStatusError):
                    await client.health_check()
            
            # Circuit breaker should be open
            assert client._circuit_breaker_open == True
            assert client._failure_count == 5
            
            # Next request should fail immediately
            with pytest.raises(Exception, match="Circuit breaker is open"):
                await client.validate_selective("test", "linkedin")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, client, mock_response):
        """Test circuit breaker recovery after timeout"""
        # Open circuit breaker
        client._circuit_breaker_open = True
        client._failure_count = 5
        client._last_failure_time = datetime.utcnow()
        
        # Simulate time passage
        client._recovery_timeout = 0.1  # 100ms for testing
        await asyncio.sleep(0.2)
        
        # Should allow request after recovery timeout
        with patch.object(client.client, 'get', return_value=mock_response):
            result = await client.health_check()
            assert result["status"] == "success"
            assert client._failure_count == 0
    
    @pytest.mark.asyncio
    async def test_batch_validation(self, client, mock_response):
        """Test batch validation functionality"""
        items = [
            {"content": "Content 1", "platform": "linkedin", "mode": "selective"},
            {"content": "Content 2", "platform": "twitter", "mode": "comprehensive"},
            {"content": "Content 3", "platform": "beehiiv", "mode": "selective"}
        ]
        
        mock_response.json.side_effect = [
            {"validation_id": f"val_{i}", "success": True}
            for i in range(3)
        ]
        
        with patch.object(client.client, 'post', return_value=mock_response):
            results = await client.validate_batch(items)
            
            assert len(results) == 3
            assert all(r["success"] for r in results)
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, client, mock_response):
        """Test cache-related operations"""
        # Test cache stats
        mock_response.json.return_value = {"total_rules": 355, "collections": 5}
        with patch.object(client.client, 'get', return_value=mock_response):
            stats = await client.get_cache_stats()
            assert stats["total_rules"] == 355
        
        # Test cache dump
        mock_response.json.return_value = [
            {"rule_id": "r1", "content": "Rule 1"},
            {"rule_id": "r2", "content": "Rule 2"}
        ]
        with patch.object(client.client, 'get', return_value=mock_response):
            dump = await client.get_cache_dump()
            assert len(dump) == 2
        
        # Test cache refresh
        mock_response.json.return_value = {"status": "refreshed", "rules_loaded": 355}
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.refresh_cache()
            assert result["status"] == "refreshed"
    
    @pytest.mark.asyncio
    async def test_benchmark_latency(self, client, mock_response):
        """Test latency benchmark functionality"""
        mock_response.json.return_value = {
            "queries": 10000,
            "p95": 150,
            "p99": 450,
            "mean": 100
        }
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.benchmark_latency(queries=10000, percentiles=[95, 99])
            
            assert result["queries"] == 10000
            assert result["p95"] == 150
            assert result["p99"] == 450
    
    @pytest.mark.asyncio
    async def test_service_info(self, client, mock_response):
        """Test service info endpoint"""
        mock_response.json.return_value = {
            "name": "editorial-service",
            "version": "2.0.0",
            "endpoints": {
                "health": "/health",
                "validate": "/validate"
            }
        }
        
        with patch.object(client.client, 'get', return_value=mock_response):
            info = await client.get_service_info()
            
            assert info["name"] == "editorial-service"
            assert info["version"] == "2.0.0"
            assert "health" in info["endpoints"]
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, client, mock_response):
        """Test readiness check"""
        mock_response.status_code = 200
        
        with patch.object(client.client, 'get', return_value=mock_response):
            ready = await client.check_readiness()
            assert ready == True
        
        # Test when not ready
        mock_response.status_code = 503
        with patch.object(client.client, 'get', return_value=mock_response):
            ready = await client.check_readiness()
            assert ready == False
    
    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling for various scenarios"""
        # Network error
        with patch.object(client.client, 'get', side_effect=httpx.NetworkError("Connection failed")):
            with pytest.raises(httpx.NetworkError):
                await client.health_check()
        
        # Timeout error
        with patch.object(client.client, 'get', side_effect=httpx.TimeoutException("Request timeout")):
            with pytest.raises(httpx.TimeoutException):
                await client.health_check()
        
        # HTTP error
        error_response = MagicMock()
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=None, response=None
        )
        with patch.object(client.client, 'get', return_value=error_response):
            with pytest.raises(httpx.HTTPStatusError):
                await client.health_check()
    
    @pytest.mark.asyncio
    async def test_create_editorial_client(self):
        """Test convenience function for client creation"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = MagicMock()
        
        with patch('ai_writing_flow.clients.editorial_client.EditorialServiceClient') as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.health_check = AsyncMock(return_value={"status": "healthy"})
            
            client = await create_editorial_client("http://test:8040")
            
            MockClient.assert_called_once_with(base_url="http://test:8040")
            mock_instance.health_check.assert_called_once()


@pytest.mark.asyncio
class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    @pytest.fixture
    async def client(self):
        """Create test client"""
        client = EditorialServiceClient()
        yield client
        await client.close()
    
    @pytest.mark.asyncio
    async def test_dual_workflow_scenario(self, client):
        """Test dual workflow (selective + comprehensive) scenario"""
        mock_response = MagicMock()
        
        # Mock selective validation
        mock_response.json.return_value = {
            "mode": "selective",
            "violations": [],
            "suggestions": ["Minor improvements"]
        }
        
        with patch.object(client.client, 'post', return_value=mock_response):
            # Human-assisted workflow
            selective_result = await client.validate_selective(
                "Draft content",
                "linkedin",
                checkpoint="style"
            )
            assert selective_result["mode"] == "selective"
            
            # AI-first workflow
            mock_response.json.return_value = {
                "mode": "comprehensive",
                "violations": [{"rule": "engagement"}],
                "suggestions": []
            }
            comprehensive_result = await client.validate_comprehensive(
                "Final content",
                "linkedin",
                content_type="article"
            )
            assert comprehensive_result["mode"] == "comprehensive"
            assert len(comprehensive_result["violations"]) == 1
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_scenario(self, client):
        """Test performance monitoring scenario"""
        mock_response = MagicMock()
        
        # Check initial stats
        mock_response.json.return_value = {"total_rules": 0}
        with patch.object(client.client, 'get', return_value=mock_response):
            stats = await client.get_cache_stats()
            assert stats["total_rules"] == 0
        
        # Refresh cache
        mock_response.json.return_value = {"status": "refreshed", "rules_loaded": 355}
        with patch.object(client.client, 'post', return_value=mock_response):
            refresh_result = await client.refresh_cache()
            assert refresh_result["rules_loaded"] == 355
        
        # Run benchmark
        mock_response.json.return_value = {"p95": 180, "p99": 450}
        with patch.object(client.client, 'post', return_value=mock_response):
            benchmark = await client.benchmark_latency(queries=1000)
            assert benchmark["p95"] < 200  # P95 < 200ms requirement
            assert benchmark["p99"] < 500  # P99 < 500ms requirement