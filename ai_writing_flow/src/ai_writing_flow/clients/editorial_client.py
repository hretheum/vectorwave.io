"""
Editorial Service HTTP Client
Provides comprehensive interface to Editorial Service for content validation
Aligned with Vector Wave ChromaDB-centric architecture
"""

import httpx
import os
from typing import Dict, List, Optional, Any, Iterable, Tuple, Callable
import logging
import asyncio
from datetime import datetime, timezone
import json
import uuid
import random

logger = logging.getLogger(__name__)


class EditorialServiceClient:
    """
    HTTP client for Editorial Service communication
    Implements both selective (human-assisted) and comprehensive (AI-first) validation workflows
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_keepalive_connections: int = 10,
        max_connections: int = 50,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.2,
        retry_on_status: Iterable[int] = (502, 503, 504),
        api_token: Optional[str] = None,
        observer: Optional[Callable[[str, float, bool, Optional[str]], None]] = None,
    ):
        """
        Initialize Editorial Service client
        
        Args:
            base_url: Editorial Service base URL (default: http://localhost:8040)
            timeout: Request timeout in seconds (default: 30.0)
        """
        # Prefer env var if base_url not provided
        resolved_base_url = base_url or os.getenv("EDITORIAL_SERVICE_URL", "http://editorial-service:8040")
        self.base_url = resolved_base_url.rstrip('/')
        self.timeout = timeout
        # Store limits for testability and diagnostics
        self._limits = httpx.Limits(
            max_keepalive_connections=max_keepalive_connections,
            max_connections=max_connections,
        )
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=self._limits,
        )
        # Base headers
        self._base_headers: Dict[str, str] = {}
        if api_token:
            self._base_headers["Authorization"] = f"Bearer {api_token}"
        # Optional observer hook: (endpoint, elapsed_ms, success, error)
        self._observer = observer
        # Retry configuration
        self._max_retries = max(1, int(max_retries))
        self._retry_backoff_factor = float(retry_backoff_factor)
        self._retry_on_status = set(int(s) for s in retry_on_status)
        self._circuit_breaker_open = False
        self._failure_count = 0
        self._failure_threshold = 5
        self._last_failure_time: Optional[datetime] = None
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
    
    async def _request_with_retries(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Execute an HTTP request with simple retry and exponential backoff.
        Retries on network errors, timeouts, and configured HTTP status codes.
        """
        if not await self._check_circuit_breaker():
            raise EditorialServiceUnavailable("Circuit breaker is open - Editorial Service unavailable")

        last_exc: Optional[Exception] = None
        for attempt in range(1, self._max_retries + 1):
            try:
                # Inject headers with auth and x-request-id
                headers = dict(self._base_headers)
                hdrs = kwargs.get("headers") or {}
                headers.update(hdrs)
                headers.setdefault("x-request-id", str(uuid.uuid4()))
                kwargs["headers"] = headers
                start = datetime.now(timezone.utc)
                # Use verb-specific method for backward compatibility with tests mocking .get/.post
                lower_method = method.lower()
                if lower_method == "get" and hasattr(self.client, "get"):
                    response = await self.client.get(url, **kwargs)
                elif lower_method == "post" and hasattr(self.client, "post"):
                    response = await self.client.post(url, **kwargs)
                else:
                    response = await self.client.request(method=method, url=url, **kwargs)
                # Retry on certain status codes without raising
                if response.status_code in self._retry_on_status and attempt < self._max_retries:
                    logger.warning(
                        "Retryable HTTP status encountered",
                        extra={
                            "status": response.status_code,
                            "attempt": attempt,
                            "url": url,
                        },
                    )
                    # Exponential backoff with jitter
                    base = self._retry_backoff_factor * (2 ** (attempt - 1))
                    sleep_s = base + random.uniform(0, base)
                    await asyncio.sleep(sleep_s)
                    continue

                response.raise_for_status()
                await self._handle_success()
                if self._observer:
                    try:
                        elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000.0
                        self._observer(url, elapsed, True, None)
                    except Exception:
                        pass
                return response
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.PoolTimeout, httpx.RemoteProtocolError) as e:
                last_exc = e
                await self._handle_failure(e)
                if attempt >= self._max_retries:
                    logger.error(
                        "HTTP request failed after retries",
                        extra={"attempts": attempt, "url": url, "error": str(e)},
                    )
                    raise EditorialServiceTimeout(str(e))
                backoff = self._retry_backoff_factor * (2 ** (attempt - 1))
                backoff += random.uniform(0, backoff)
                logger.info(
                    "Retrying HTTP request",
                    extra={"attempt": attempt, "backoff_seconds": backoff, "url": url},
                )
                await asyncio.sleep(backoff)
            except httpx.HTTPStatusError as e:
                # Non-retryable status or final attempt of retryable one
                last_exc = e
                await self._handle_failure(e)
                logger.error("Non-retryable HTTP status or final attempt failed", extra={"url": url, "error": str(e)})
                raise EditorialServiceError(str(e))
            except Exception as e:
                last_exc = e
                await self._handle_failure(e)
                logger.error("Unexpected error during HTTP request", extra={"url": url, "error": str(e)})
                raise EditorialServiceError(str(e))

        # Should not reach here due to returns/raises above
        if last_exc:
            raise last_exc
        raise RuntimeError("Request failed without specific exception")

    async def _check_circuit_breaker(self):
        """Check if circuit breaker should be open or closed"""
        if not self._circuit_breaker_open:
            return True
            
        if self._last_failure_time:
            time_since_failure = (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
            if time_since_failure > self._recovery_timeout:
                logger.info("Circuit breaker recovery timeout reached, attempting to close")
                self._circuit_breaker_open = False
                self._failure_count = 0
                return True
                
        return False
    
    async def _handle_failure(self, error: Exception):
        """Handle request failure and update circuit breaker state"""
        self._failure_count += 1
        self._last_failure_time = datetime.now(timezone.utc)
        
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
        response = await self._request_with_retries("GET", f"{self.base_url}/health", timeout=10.0)
        return response.json()
    
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
        payload = {
            "content": content,
            "platform": platform,
            "mode": "selective",
            "checkpoint": checkpoint,
            "context": {
                "checkpoint": checkpoint,
                **(context or {})
            }
        }
        
        response = await self._request_with_retries(
            "POST",
            f"{self.base_url}/validate/selective",
            json=payload,
            timeout=10.0,
        )
        return response.json()
    
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
        payload = {
            "content": content,
            "platform": platform,
            "content_type": content_type,
            "context": context or {}
        }
        
        response = await self._request_with_retries(
            "POST",
            f"{self.base_url}/validate/comprehensive",
            json=payload,
            timeout=30.0,
        )
        return response.json()
    
    async def get_cache_stats(self) -> Dict:
        """
        Get ChromaDB cache statistics
        
        Returns:
            Dict with cache statistics including rule count
        """
        response = await self._request_with_retries("GET", f"{self.base_url}/cache/stats", timeout=10.0)
        return response.json()
    
    async def get_cache_dump(self) -> List[Dict]:
        """
        Get full cache dump for verification
        
        Returns:
            List of cached rules with metadata
        """
        response = await self._request_with_retries("GET", f"{self.base_url}/cache/dump", timeout=10.0)
        return response.json()
    
    async def refresh_cache(self) -> Dict:
        """
        Trigger cache refresh from ChromaDB
        
        Returns:
            Dict with refresh status
        """
        response = await self._request_with_retries("POST", f"{self.base_url}/cache/refresh", timeout=15.0)
        return response.json()
    
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
        
        response = await self._request_with_retries(
            "POST",
            f"{self.base_url}/benchmark/latency",
            json=payload,
            timeout=120.0,  # Extended timeout for benchmarks
        )
        return response.json()
    
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
        response = await self._request_with_retries("GET", f"{self.base_url}/info", timeout=10.0)
        return response.json()
    
    async def check_readiness(self) -> bool:
        """
        Check if Editorial Service is ready to handle requests
        
        Returns:
            True if service is ready, False otherwise
        """
        try:
            response = await self._request_with_retries("GET", f"{self.base_url}/ready", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    # --- Sync convenience wrappers ---
    def validate_selective_sync(self, content: str, platform: str, checkpoint: str = "general", context: Optional[Dict] = None) -> Dict:
        return asyncio.run(self.validate_selective(content, platform, checkpoint, context))

    def validate_comprehensive_sync(self, content: str, platform: str, content_type: str = "article", context: Optional[Dict] = None) -> Dict:
        return asyncio.run(self.validate_comprehensive(content, platform, content_type, context))

    def get_cache_stats_sync(self) -> Dict:
        return asyncio.run(self.get_cache_stats())

    def health_check_sync(self) -> Dict:
        return asyncio.run(self.health_check())


class EditorialServiceError(Exception):
    pass


class EditorialServiceUnavailable(EditorialServiceError):
    pass


class EditorialServiceTimeout(EditorialServiceError):
    pass


# Convenience functions for quick usage
async def create_editorial_client(base_url: Optional[str] = None) -> EditorialServiceClient:
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