"""
ChromaDB Async Client (HTTP) for health and basic operations.

Uses HTTP endpoints to avoid tight coupling with the Python SDK in early phases.
"""
from __future__ import annotations

import os
import time
import asyncio
from typing import Any, Dict, Optional

import httpx
import structlog

logger = structlog.get_logger()


class ChromaDBHTTPClient:
    """Lightweight async HTTP client for ChromaDB server."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        self.host: str = host or os.getenv("CHROMADB_HOST", "localhost")
        self.port: int = int(port or os.getenv("CHROMADB_PORT", "8000"))
        # Support both Chroma v1 and v2 HTTP APIs
        self.base_url_v1: str = f"http://{self.host}:{self.port}/api/v1"
        self.base_url_v2: str = f"http://{self.host}:{self.port}/api/v2"
        self._last_healthy: Optional[float] = None
        self._initialized: bool = False
        self._connection_attempts: int = 0
        self._connection_failures: int = 0
        
    async def wait_for_connection(self, max_retries: int = 10, initial_delay: float = 2.0) -> bool:
        """Wait for ChromaDB to be available with exponential backoff.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            
        Returns:
            True if connection established, False otherwise
        """
        delay = initial_delay
        
        for attempt in range(max_retries):
            self._connection_attempts += 1
            logger.info(
                "Attempting ChromaDB connection",
                attempt=attempt + 1,
                max_retries=max_retries,
                host=self.host,
                port=self.port
            )
            
            result = await self.heartbeat()
            if result.get("status") == "healthy":
                logger.info(
                    "ChromaDB connection established",
                    attempts=attempt + 1,
                    latency_ms=result.get("latency_ms")
                )
                self._initialized = True
                return True
                
            self._connection_failures += 1
            logger.warning(
                "ChromaDB connection failed, retrying",
                attempt=attempt + 1,
                delay=delay,
                error=result.get("error")
            )
            
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30.0)  # Exponential backoff, max 30s
                
        logger.error(
            "ChromaDB connection failed after all retries",
            attempts=max_retries,
            host=self.host,
            port=self.port
        )
        return False

    async def heartbeat(self) -> Dict[str, Any]:
        """Call ChromaDB heartbeat endpoint and return status + latency."""
        # Prefer v2 heartbeat if available, fallback to v1
        url_v2 = f"{self.base_url_v2}/heartbeat"
        url_v1 = f"{self.base_url_v1}/heartbeat"
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # Try v2 first
                resp = await client.get(url_v2)
                latency_ms = (time.time() - start) * 1000.0
                if resp.status_code == 200:
                    self._last_healthy = time.time()
                    return {
                        "status": "healthy",
                        "latency_ms": round(latency_ms, 2),
                        "api_version": "v2",
                    }
                # If v2 not available or returns non-200, try v1
                resp = await client.get(url_v1)
                latency_ms = (time.time() - start) * 1000.0
                if resp.status_code == 200:
                    self._last_healthy = time.time()
                    return {
                        "status": "healthy",
                        "latency_ms": round(latency_ms, 2),
                        "api_version": "v1",
                    }
                return {
                    "status": "unhealthy",
                    "latency_ms": round(latency_ms, 2),
                    "error": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            latency_ms = (time.time() - start) * 1000.0
            return {"status": "unavailable", "latency_ms": round(latency_ms, 2), "error": str(e)}

    async def collections_count(self) -> Dict[str, Any]:
        """Return number of collections if accessible (best-effort)."""
        # Collections endpoint differs between API versions. We best-effort
        # attempt v1 (legacy) and otherwise return 0.
        url_v1 = f"{self.base_url_v1}/collections"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(url_v1)
                if resp.status_code == 200:
                    data = resp.json()
                    return {"collections": len(data)} if isinstance(data, list) else {"collections": 0}
                return {"collections": 0, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"collections": 0, "error": str(e)}

    def info(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "base_url_v1": self.base_url_v1,
            "base_url_v2": self.base_url_v2,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "initialized": self._initialized,
            "connection_attempts": self._connection_attempts,
            "connection_failures": self._connection_failures,
            "last_healthy": self._last_healthy,
        }
