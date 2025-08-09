"""
ChromaDB Async Client (HTTP) for health and basic operations.

Uses HTTP endpoints to avoid tight coupling with the Python SDK in early phases.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import httpx


class ChromaDBHTTPClient:
    """Lightweight async HTTP client for ChromaDB server."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        self.host: str = host or os.getenv("CHROMADB_HOST", "localhost")
        self.port: int = int(port or os.getenv("CHROMADB_PORT", "8000"))
        # Support both Chroma v1 and v2 HTTP APIs
        self.base_url_v1: str = f"http://{self.host}:{self.port}/api/v1"
        self.base_url_v2: str = f"http://{self.host}:{self.port}/api/v2"
        self._last_healthy: Optional[float] = None

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
                    }
                # If v2 not available or returns non-200, try v1
                resp = await client.get(url_v1)
                latency_ms = (time.time() - start) * 1000.0
                if resp.status_code == 200:
                    self._last_healthy = time.time()
                    return {
                        "status": "healthy",
                        "latency_ms": round(latency_ms, 2),
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
