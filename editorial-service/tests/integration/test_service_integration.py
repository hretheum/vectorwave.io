"""
Integration tests for Editorial Service
Tests Docker compose setup, service discovery, and ecosystem integration
"""
import pytest
import asyncio
import httpx
import redis.asyncio as redis
from datetime import datetime
import time
import docker
import subprocess
import os


@pytest.mark.integration
class TestContainerIntegration:
    """Test Docker container and compose integration"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client fixture"""
        return docker.from_env()
    
    @pytest.fixture(scope="class")
    def service_base_url(self):
        """Base URL for the service"""
        return "http://localhost:8040"
    
    @pytest.mark.slow
    async def test_service_container_health(self, service_base_url):
        """Test service container is healthy and responding"""
        timeout = 30
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{service_base_url}/health", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        assert data["status"] in ["healthy", "degraded"]
                        assert data["service"] == "editorial-service"
                        return
            except (httpx.RequestError, httpx.TimeoutException):
                await asyncio.sleep(2)
        
        pytest.fail("Service did not become healthy within timeout")
    
    @pytest.mark.slow
    async def test_metrics_endpoint_integration(self, service_base_url):
        """Test metrics endpoint returns Prometheus metrics"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{service_base_url}/metrics")
            assert response.status_code == 200
            
            content = response.text
            assert "http_requests_total" in content
            assert "http_request_duration_seconds" in content
            assert "active_connections_total" in content
            assert "service_info" in content
    
    async def test_service_info_integration(self, service_base_url):
        """Test service info endpoint for service discovery"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{service_base_url}/info")
            assert response.status_code == 200
            
            data = response.json()
            assert data["name"] == "editorial-service"
            assert data["version"] == "2.0.0"
            assert data["port"] == 8040
            
            # Check endpoints are defined
            endpoints = data["endpoints"]
            required_endpoints = ["health", "metrics", "info", "ready"]
            for endpoint in required_endpoints:
                assert endpoint in endpoints
    
    async def test_readiness_probe_integration(self, service_base_url):
        """Test Kubernetes readiness probe"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{service_base_url}/ready")
            assert response.status_code in [200, 503]
            
            data = response.json()
            assert "status" in data
            assert data["status"] in ["ready", "not_ready"]


@pytest.mark.integration
@pytest.mark.redis
class TestRedisIntegration:
    """Test Redis integration and service discovery"""
    
    @pytest.fixture(scope="class")
    def redis_client(self):
        """Redis client for testing"""
        client = redis.from_url("redis://localhost:6379")
        yield client
        asyncio.run(client.close())
    
    @pytest.mark.asyncio
    async def test_redis_connection(self, redis_client):
        """Test Redis is accessible"""
        try:
            await redis_client.ping()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_service_registration(self, redis_client):
        """Test service registers itself in Redis"""
        # Wait a bit for service to register
        await asyncio.sleep(5)
        
        service_key = "vector-wave:services:editorial-service"
        service_data = await redis_client.hgetall(service_key)
        
        if not service_data:
            pytest.skip("Service not yet registered in Redis")
        
        # Convert bytes to string for assertions
        service_data = {k.decode(): v.decode() for k, v in service_data.items()}
        
        assert service_data["name"] == "editorial-service"
        assert service_data["version"] == "2.0.0"
        assert "last_heartbeat" in service_data
        
        # Check heartbeat is recent (within last minute)
        heartbeat_time = datetime.fromisoformat(service_data["last_heartbeat"])
        time_diff = datetime.utcnow() - heartbeat_time
        assert time_diff.total_seconds() < 60


@pytest.mark.integration
@pytest.mark.network
class TestNetworkIntegration:
    """Test Docker network integration"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        return docker.from_env()
    
    def test_shared_network_exists(self, docker_client):
        """Test vector-wave-shared network exists"""
        try:
            network = docker_client.networks.get("vector-wave-shared")
            assert network.name == "vector-wave-shared"
        except docker.errors.NotFound:
            pytest.skip("vector-wave-shared network not found")
    
    def test_service_connected_to_shared_network(self, docker_client):
        """Test editorial service is connected to shared network"""
        try:
            network = docker_client.networks.get("vector-wave-shared")
            containers = network.containers
            
            # Look for editorial service container
            editorial_containers = [c for c in containers if "editorial" in c.name]
            assert len(editorial_containers) > 0, "Editorial service not connected to shared network"
            
        except docker.errors.NotFound:
            pytest.skip("vector-wave-shared network not found")


@pytest.mark.integration
@pytest.mark.observability
class TestObservabilityIntegration:
    """Test observability stack integration"""
    
    @pytest.fixture
    def prometheus_url(self):
        return "http://localhost:9090"
    
    @pytest.fixture
    def jaeger_url(self):
        return "http://localhost:16686"
    
    @pytest.mark.slow
    async def test_prometheus_scraping(self, prometheus_url):
        """Test Prometheus is scraping metrics"""
        try:
            async with httpx.AsyncClient() as client:
                # Check if Prometheus is running
                response = await client.get(f"{prometheus_url}/api/v1/status/config")
                if response.status_code != 200:
                    pytest.skip("Prometheus not running")
                
                # Check if editorial-service target is configured
                response = await client.get(f"{prometheus_url}/api/v1/targets")
                data = response.json()
                
                targets = data["data"]["activeTargets"]
                editorial_targets = [t for t in targets if "editorial-service" in t["job"]]
                
                if not editorial_targets:
                    pytest.skip("Editorial service not configured in Prometheus")
                
                # Check if at least one target is healthy
                healthy_targets = [t for t in editorial_targets if t["health"] == "up"]
                assert len(healthy_targets) > 0, "No healthy editorial service targets"
                
        except httpx.RequestError:
            pytest.skip("Prometheus not accessible")
    
    @pytest.mark.slow 
    async def test_jaeger_availability(self, jaeger_url):
        """Test Jaeger is running and accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{jaeger_url}/api/services")
                assert response.status_code == 200
                
        except httpx.RequestError:
            pytest.skip("Jaeger not accessible")


@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceIntegration:
    """Test performance in integrated environment"""
    
    @pytest.fixture
    def service_base_url(self):
        return "http://localhost:8040"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, service_base_url):
        """Test service handles concurrent requests well"""
        concurrent_requests = 50
        
        async def make_request():
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                response = await client.get(f"{service_base_url}/health")
                end_time = time.time()
                return response.status_code, end_time - start_time
        
        # Make concurrent requests
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful_requests = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_requests) >= concurrent_requests * 0.95  # 95% success rate
        
        # Check response times
        response_times = [result[1] for result in successful_requests if len(result) == 2]
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 1.0, f"Average response time too high: {avg_response_time}"
    
    @pytest.mark.asyncio
    async def test_metrics_collection_performance(self, service_base_url):
        """Test metrics collection doesn't impact performance significantly"""
        # Make requests to generate metrics
        async with httpx.AsyncClient() as client:
            for _ in range(10):
                await client.get(f"{service_base_url}/health")
            
            # Test metrics endpoint performance
            start_time = time.time()
            response = await client.get(f"{service_base_url}/metrics")
            end_time = time.time()
            
            assert response.status_code == 200
            metrics_response_time = end_time - start_time
            assert metrics_response_time < 0.5, "Metrics endpoint too slow"


@pytest.mark.integration
@pytest.mark.ecosystem
class TestEcosystemIntegration:
    """Test integration with Vector Wave ecosystem"""
    
    @pytest.fixture
    def service_base_url(self):
        return "http://localhost:8040"
    
    @pytest.mark.asyncio
    async def test_service_discovery_data_structure(self, service_base_url):
        """Test service exposes correct data for ecosystem discovery"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{service_base_url}/info")
            data = response.json()
            
            # Check required fields for ecosystem integration
            required_fields = ["name", "version", "environment", "port", "endpoints"]
            for field in required_fields:
                assert field in data
            
            # Check endpoints structure
            endpoints = data["endpoints"]
            assert isinstance(endpoints, dict)
            assert len(endpoints) >= 3  # At least health, metrics, info
    
    @pytest.mark.asyncio 
    async def test_health_check_ecosystem_format(self, service_base_url):
        """Test health check returns ecosystem-compatible format"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{service_base_url}/health")
            data = response.json()
            
            # Check ecosystem-required fields
            assert "status" in data
            assert "service" in data
            assert "version" in data
            assert "environment" in data
            assert "checks" in data
            assert "timestamp" in data
            
            # Check checks structure
            checks = data["checks"]
            assert isinstance(checks, dict)
            
            # Each check should have status
            for check_name, check_data in checks.items():
                assert "status" in check_data
                assert check_data["status"] in ["healthy", "unhealthy", "unavailable"]


@pytest.mark.integration
@pytest.mark.slow
class TestDockerComposeIntegration:
    """Test full Docker Compose setup"""
    
    def test_compose_services_running(self):
        """Test all services defined in compose are running"""
        try:
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.dev.yml", "ps", "--services", "--filter", "status=running"],
                capture_output=True,
                text=True,
                cwd="/Users/hretheum/dev/bezrobocie/vector-wave/editorial-service"
            )
            
            if result.returncode != 0:
                pytest.skip("Docker compose not running")
            
            running_services = result.stdout.strip().split('\n')
            running_services = [s for s in running_services if s]  # Remove empty strings
            
            expected_services = ["editorial-service"]  # Minimum required
            for service in expected_services:
                assert service in running_services, f"Service {service} not running"
                
        except FileNotFoundError:
            pytest.skip("Docker compose not available")