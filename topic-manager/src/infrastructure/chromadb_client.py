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

    async def _get_collection_id(self, client: httpx.AsyncClient, name: str) -> str | None:
        # Try by query param first
        resp = await client.get(f"{self.base_url_v1}/collections", params={"name": name})
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("id"):
                return data.get("id") or data.get("uuid")
        # Fallback to list all
        resp = await client.get(f"{self.base_url_v1}/collections")
        if resp.status_code == 200 and isinstance(resp.json(), list):
            for c in resp.json():
                if c.get("name") == name:
                    return c.get("id") or c.get("uuid")
        return None

    async def delete_collection(self, name: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                # Accept name or id; resolve name to id
                col_id = await self._get_collection_id(client, name)
                url = f"{self.base_url_v1}/collections/{col_id or name}"
                resp = await client.delete(url)
                return resp.status_code in (200, 204)
        except Exception:
            return False

    async def count(self, name: str) -> int:
        # No direct count endpoint in v1; we can approximate by listing (not ideal).
        # Many servers expose GET /collections/{name} which includes size; attempt that.
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                col_id = await self._get_collection_id(client, name)
                if not col_id:
                    return 0
                url = f"{self.base_url_v1}/collections/{col_id}"
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
            async with httpx.AsyncClient(timeout=12.0) as client:
                col_id = await self._get_collection_id(client, name)
                if not col_id:
                    return False
                url = f"{self.base_url_v1}/collections/{col_id}/add"
                payload: Dict[str, Any] = {"ids": ids, "documents": documents}
                if metadatas is not None:
                    payload["metadatas"] = metadatas
                if embeddings is not None:
                    payload["embeddings"] = embeddings
                resp = await client.post(url, json=payload)
                return resp.status_code in (200, 201)
        except Exception:
            return False

    async def query(self, name: str, query_embeddings: List[List[float]], n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                col_id = await self._get_collection_id(client, name)
                if not col_id:
                    return {}
                url = f"{self.base_url_v1}/collections/{col_id}/query"
                payload: Dict[str, Any] = {"query_embeddings": query_embeddings, "n_results": n_results}
                if where:
                    payload["where"] = where
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return {"ids": [], "distances": [], "documents": [], "metadatas": []}

    async def get(self, name: str, ids: List[str]) -> Dict[str, Any]:
        """Get items by IDs from a collection (best-effort)."""
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                col_id = await self._get_collection_id(client, name)
                if not col_id:
                    return {}
                url = f"{self.base_url_v1}/collections/{col_id}/get"
                resp = await client.post(url, json={"ids": ids})
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return {}
