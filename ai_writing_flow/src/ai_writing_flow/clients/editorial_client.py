"""
Editorial Service HTTP Client
Provides comprehensive interface to Editorial Service for content validation
Aligned with Vector Wave ChromaDB-centric architecture
"""

import httpx
from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class EditorialServiceClient:
    """
    HTTP client for Editorial Service communication
    Implements both selective (human-assisted) and comprehensive (AI-first) validation workflows
    """
    
    def __init__(self, base_url: str = "http://localhost:8040", timeout: float = 30.0):
        """
        Initialize Editorial Service client
        
        Args:
            base_url: Editorial Service base URL (default: http://localhost:8040)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=50)
        )
        self._circuit_breaker_open = False
        self._failure_count = 0
        self._failure_threshold = 5
        self._last_failure_time = None
        self._recovery_timeout = 60  # seconds
        
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def _check_circuit_breaker(self):
        """Check if circuit breaker should be open or closed"""
        if not self._circuit_breaker_open:
            return True
            
        if self._last_failure_time:
            time_since_failure = (datetime.utcnow() - self._last_failure_time).total_seconds()
            if time_since_failure > self._recovery_timeout:
                logger.info("Circuit breaker recovery timeout reached, attempting to close")
                self._circuit_breaker_open = False
                self._failure_count = 0
                return True
                
        return False
    
    async def _handle_failure(self, error: Exception):
        """Handle request failure and update circuit breaker state"""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        
        if self._failure_count >= self._failure_threshold:
            self._circuit_breaker_open = True
            logger.error(f"Circuit breaker opened after {self._failure_count} failures")
            
    async def _handle_success(self):
        """Handle successful request"""
        if self._failure_count > 0:
            self._failure_count = 0
            logger.info("Request successful, resetting failure count")
            
    async def health_check(self) -> Dict:
        """
        Check Editorial Service health
        
        Returns:
            Dict with health status information
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            await self._handle_success()
            return response.json()
        except httpx.HTTPError as e:
            await self._handle_failure(e)
            logger.error(f"Editorial service health check failed: {e}")
            raise
    
    async def validate_selective(self, 
                                content: str, 
                                platform: str,
                                checkpoint: str = "general",
                                context: Optional[Dict] = None) -> Dict:
        """
        Selective validation for human-assisted workflow
        Uses 3-4 most critical rules per checkpoint
        
        Args:
            content: Content to validate
            platform: Target platform (linkedin, twitter, beehiiv, ghost)
            checkpoint: Validation checkpoint (general, style, audience, quality)
            context: Additional context for validation
            
        Returns:
            Dict with validation results including violations and suggestions
        """
        if not await self._check_circuit_breaker():
            raise Exception("Circuit breaker is open - Editorial Service unavailable")
            
        payload = {
            "content": content,
            "platform": platform,
            "mode": "selective",
            "context": {
                "checkpoint": checkpoint,
                **(context or {})
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/validate/selective",
                json=payload
            )
            response.raise_for_status()
            await self._handle_success()
            return response.json()
            
        except httpx.HTTPError as e:
            await self._handle_failure(e)
            logger.error(f"Editorial service selective validation failed: {e}")
            raise
    
    async def validate_comprehensive(self,
                                    content: str,
                                    platform: str,
                                    content_type: str = "article",
                                    context: Optional[Dict] = None) -> Dict:
        """
        Comprehensive validation for AI-first workflow
        Uses 8-12 rules for thorough validation
        
        Args:
            content: Content to validate
            platform: Target platform
            content_type: Type of content (article, thread, newsletter)
            context: Additional validation context
            
        Returns:
            Dict with comprehensive validation results
        """
        if not await self._check_circuit_breaker():
            raise Exception("Circuit breaker is open - Editorial Service unavailable")
            
        payload = {
            "content": content,
            "platform": platform,
            "content_type": content_type,
            "context": context or {}
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/validate/comprehensive",
                json=payload
            )
            response.raise_for_status()
            await self._handle_success()
            return response.json()
            
        except httpx.HTTPError as e:
            await self._handle_failure(e)
            logger.error(f"Editorial service comprehensive validation failed: {e}")
            raise
    
    async def get_cache_stats(self) -> Dict:
        """
        Get ChromaDB cache statistics
        
        Returns:
            Dict with cache statistics including rule count
        """
        try:
            response = await self.client.get(f"{self.base_url}/cache/stats")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get cache stats: {e}")
            raise
    
    async def get_cache_dump(self) -> List[Dict]:
        """
        Get full cache dump for verification
        
        Returns:
            List of cached rules with metadata
        """
        try:
            response = await self.client.get(f"{self.base_url}/cache/dump")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get cache dump: {e}")
            raise
    
    async def refresh_cache(self) -> Dict:
        """
        Trigger cache refresh from ChromaDB
        
        Returns:
            Dict with refresh status
        """
        try:
            response = await self.client.post(f"{self.base_url}/cache/refresh")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to refresh cache: {e}")
            raise
    
    async def benchmark_latency(self, queries: int = 10000, percentiles: List[int] = None) -> Dict:
        """
        Run latency benchmark
        
        Args:
            queries: Number of queries to run
            percentiles: Percentiles to report (default: [95, 99])
            
        Returns:
            Dict with benchmark results
        """
        if percentiles is None:
            percentiles = [95, 99]
            
        payload = {
            "queries": queries,
            "report_percentiles": percentiles
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/benchmark/latency",
                json=payload,
                timeout=120.0  # Extended timeout for benchmarks
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Benchmark failed: {e}")
            raise
    
    async def validate_batch(self, items: List[Dict]) -> List[Dict]:
        """
        Batch validation for multiple content items
        
        Args:
            items: List of dicts with content, platform, and mode
            
        Returns:
            List of validation results
        """
        results = []
        
        # Process in parallel with concurrency limit
        semaphore = asyncio.Semaphore(5)
        
        async def validate_item(item):
            async with semaphore:
                try:
                    if item.get("mode") == "selective":
                        result = await self.validate_selective(
                            content=item["content"],
                            platform=item["platform"],
                            checkpoint=item.get("checkpoint", "general"),
                            context=item.get("context")
                        )
                    else:
                        result = await self.validate_comprehensive(
                            content=item["content"],
                            platform=item["platform"],
                            content_type=item.get("content_type", "article"),
                            context=item.get("context")
                        )
                    return {"success": True, "result": result}
                except Exception as e:
                    return {"success": False, "error": str(e)}
        
        tasks = [validate_item(item) for item in items]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def get_service_info(self) -> Dict:
        """
        Get Editorial Service information
        
        Returns:
            Dict with service info including version and endpoints
        """
        try:
            response = await self.client.get(f"{self.base_url}/info")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get service info: {e}")
            raise
    
    async def check_readiness(self) -> bool:
        """
        Check if Editorial Service is ready to handle requests
        
        Returns:
            True if service is ready, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/ready")
            return response.status_code == 200
        except:
            return False


# Convenience functions for quick usage
async def create_editorial_client(base_url: str = "http://localhost:8040") -> EditorialServiceClient:
    """
    Create and return an Editorial Service client
    
    Args:
        base_url: Editorial Service base URL
        
    Returns:
        Configured EditorialServiceClient instance
    """
    client = EditorialServiceClient(base_url=base_url)
    
    # Verify connection
    try:
        await client.health_check()
        logger.info(f"Successfully connected to Editorial Service at {base_url}")
    except Exception as e:
        logger.warning(f"Editorial Service at {base_url} is not available: {e}")
    
    return client