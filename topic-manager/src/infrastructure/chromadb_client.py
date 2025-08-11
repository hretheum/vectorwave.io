from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import httpx


class ChromaDBHTTPClient:
    """Lightweight async HTTP client for ChromaDB server (best-effort v1/v2).

    This client only uses portable HTTP endpoints so Topic Manager does not
    depend on the Python SDK. All operations are best-effort and gracefully
    degrade when ChromaDB is unavailable.
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        self.host: str = host or os.getenv("CHROMADB_HOST", "localhost")
        self.port: int = int(port or os.getenv("CHROMADB_PORT", "8000"))
        self.base_url_v1: str = f"http://{self.host}:{self.port}/api/v1"
        self.base_url_v2: str = f"http://{self.host}:{self.port}/api/v2"

    async def heartbeat(self) -> Dict[str, Any]:
        url_v2 = f"{self.base_url_v2}/heartbeat"
        url_v1 = f"{self.base_url_v1}/heartbeat"
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(url_v2)
                latency_ms = round((time.time() - start) * 1000.0, 2)
                if resp.status_code == 200:
                    return {"status": "healthy", "latency_ms": latency_ms}
                resp = await client.get(url_v1)
                latency_ms = round((time.time() - start) * 1000.0, 2)
                if resp.status_code == 200:
                    return {"status": "healthy", "latency_ms": latency_ms}
                return {"status": "unhealthy", "latency_ms": latency_ms, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"status": "unavailable", "latency_ms": round((time.time() - start) * 1000.0, 2), "error": str(e)}

    async def ensure_collection(self, name: str) -> bool:
        """Create collection if missing. Returns True if ready, False otherwise."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                # List collections (v1)
                list_url = f"{self.base_url_v1}/collections"
                resp = await client.get(list_url)
                if resp.status_code == 200 and isinstance(resp.json(), list):
                    collections = resp.json()
                    if any((c.get("name") == name or c.get("id") == name) for c in collections):
                        return True
                # Try to create (v1)
                create_url = f"{self.base_url_v1}/collections"
                resp = await client.post(create_url, json={"name": name})
                return resp.status_code in (200, 201)
        except Exception:
            return False

    async def count(self, name: str) -> int:
        # No direct count endpoint in v1; we can approximate by listing (not ideal).
        # Many servers expose GET /collections/{name} which includes size; attempt that.
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                url = f"{self.base_url_v1}/collections/{name}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for key in ("size", "count", "num_vectors"):
                        if isinstance(data, dict) and key in data and isinstance(data[key], int):
                            return int(data[key])
        except Exception:
            pass
        return 0

    async def add(self, name: str, ids: List[str], documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, embeddings: Optional[List[List[float]]] = None) -> bool:
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                url = f"{self.base_url_v1}/collections/{name}/add"
                payload: Dict[str, Any] = {"ids": ids, "documents": documents}
                if metadatas is not None:
                    payload["metadatas"] = metadatas
                if embeddings is not None:
                    payload["embeddings"] = embeddings
                resp = await client.post(url, json=payload)
                return resp.status_code in (200, 201)
        except Exception:
            return False

    async def query(self, name: str, query_embeddings: List[List[float]], n_results: int = 5) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                url = f"{self.base_url_v1}/collections/{name}/query"
                resp = await client.post(url, json={"query_embeddings": query_embeddings, "n_results": n_results})
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return {"ids": [], "distances": [], "documents": [], "metadatas": []}
