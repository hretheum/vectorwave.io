"""
Unit tests for main FastAPI application
Tests observability, metrics, health checks, and service discovery
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from src.main import app, get_redis_client, register_service, health_check_redis


class TestFastAPIApplication:
    """Test FastAPI application setup and configuration"""
    
    def test_app_configuration(self):
        """Test basic app configuration"""
        assert app.title == "Editorial Service"
        assert app.version == "2.0.0"
        assert "Production-ready Vector Wave Editorial Service" in app.description
    
    def test_cors_middleware(self):
        """Test CORS middleware is properly configured"""
        # CORS middleware should be in the middleware stack
        middleware_types = [type(m) for m in app.user_middleware]
        from fastapi.middleware.cors import CORSMiddleware
        assert any(issubclass(m, CORSMiddleware) for m in middleware_types)


class TestHealthEndpoints:
    """Test health check and readiness endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)
    
    def test_health_endpoint_structure(self, client):
        """Test health endpoint returns correct structure"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["status", "service", "version", "environment", "uptime_seconds", "checks", "timestamp"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    
    def test_health_endpoint_values(self, client):
        """Test health endpoint returns expected values"""
        response = client.get("/health")
        data = response.json()
        
        assert data["service"] == "editorial-service"
        assert data["version"] == "2.0.0"
        assert data["status"] in ["healthy", "degraded"]
        assert isinstance(data["uptime_seconds"], (int, float))
        assert isinstance(data["checks"], dict)
    
    def test_readiness_endpoint(self, client):
        """Test readiness endpoint for Kubernetes"""
        response = client.get("/ready")
        assert response.status_code in [200, 503]
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] in ["ready", "not_ready"]
    
    def test_info_endpoint(self, client):
        """Test service info endpoint"""
        response = client.get("/info")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["name", "version", "environment", "port", "endpoints"]
        
        for field in required_fields:
            assert field in data
        
        assert data["name"] == "editorial-service"
        assert data["version"] == "2.0.0"
        assert isinstance(data["endpoints"], dict)


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint returns Prometheus format"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        
        # Check for basic Prometheus metrics
        content = response.text
        assert "http_requests_total" in content
        assert "http_request_duration_seconds" in content
        assert "active_connections_total" in content


class TestRedisIntegration:
    """Test Redis client and service discovery"""
    
    @pytest.mark.asyncio
    async def test_get_redis_client_success(self):
        """Test successful Redis client creation"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping = AsyncMock()
            
            client = await get_redis_client()
            
            assert client is not None
            mock_redis.assert_called_once()
            mock_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_redis_client_failure(self):
        """Test Redis client creation failure"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            client = await get_redis_client()
            
            assert client is None
    
    @pytest.mark.asyncio
    async def test_register_service_success(self):
        """Test successful service registration"""
        mock_client = AsyncMock()
        
        with patch('src.main.get_redis_client', return_value=mock_client):
            await register_service()
            
            mock_client.hset.assert_called_once()
            mock_client.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_service_failure(self):
        """Test service registration failure handling"""
        with patch('src.main.get_redis_client', side_effect=Exception("Redis error")):
            # Should not raise exception
            await register_service()
    
    @pytest.mark.asyncio
    async def test_health_check_redis_success(self):
        """Test Redis health check success"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        
        with patch('src.main.get_redis_client', return_value=mock_client):
            result = await health_check_redis()
            
            assert result["status"] == "healthy"
            mock_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_redis_failure(self):
        """Test Redis health check failure"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Connection failed"))

        from src.main import app_state
        app_state.health_checks.clear()

        with patch('src.main.get_redis_client', return_value=mock_client):
            result = await health_check_redis()
            
            assert result["status"] == "unhealthy"
            assert "Connection failed" in result["error"]


class TestMiddleware:
    """Test custom middleware functionality"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_metrics_middleware_request_count(self, client):
        """Test that middleware records request metrics"""
        # Make a request to trigger middleware
        response = client.get("/health")
        assert response.status_code == 200
        
        # Check metrics endpoint for recorded requests
        metrics_response = client.get("/metrics")
        content = metrics_response.text
        
        # Should contain request count metrics
        assert "http_requests_total" in content
        assert "http_request_duration_seconds" in content
    
    def test_metrics_middleware_different_endpoints(self, client):
        """Test middleware records different endpoints correctly"""
        # Make requests to different endpoints
        client.get("/health")
        client.get("/info")
        client.get("/ready")
        
        metrics_response = client.get("/metrics")
        content = metrics_response.text
        
        # Should record different endpoints
        assert "/health" in content or "health" in content
        assert "/info" in content or "info" in content


class TestErrorHandling:
    """Test global error handling"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_404_error(self, client):
        """Test 404 handling for non-existent endpoints"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed handling"""
        response = client.post("/health")  # GET-only endpoint
        assert response.status_code == 405


@pytest.mark.integration
class TestApplicationLifecycle:
    """Test application startup and shutdown"""
    
    @pytest.mark.asyncio
    async def test_lifespan_startup(self):
        """Test application startup lifecycle"""
        from src.main import app_state

        # Mock the lifespan context manager
        with patch('src.main.register_service') as mock_register:
            # Test startup would set startup_time
            assert hasattr(app_state, "startup_time")
            # In real startup, register_service would be called
    
    def test_app_state_initialization(self):
        """Test initial application state"""
        from src.main import app_state

        assert hasattr(app_state, "redis_client")
        assert hasattr(app_state, "startup_time")
        assert hasattr(app_state, "health_checks")


@pytest.mark.performance 
class TestPerformanceMetrics:
    """Test performance and resource usage"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_endpoint_performance(self, client):
        """Test health endpoint response time"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Health check should be fast (< 1 second)
        assert response_time < 1.0
    
    def test_metrics_endpoint_performance(self, client):
        """Test metrics endpoint performance"""
        import time
        
        start_time = time.time()
        response = client.get("/metrics")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Metrics endpoint should be fast
        assert response_time < 0.5