from typing import List, Dict, Any
from .models import RawTrendItem
import httpx
import uuid


class StorageService:
    def __init__(self, host: str, port: int, collection: str) -> None:
        self._host = host
        self._port = port
        self._collection = collection

    async def _get_collection_id(self, client: httpx.AsyncClient) -> str:
        # Try query by name param
        r = await client.get(f"http://{self._host}:{self._port}/api/v1/collections", params={"name": self._collection})
        if r.status_code == 200:
            data = r.json()
            # Chroma may return single object or list depending on version
            if isinstance(data, dict) and data.get("id"):
                return data["id"]
            if isinstance(data, list):
                for c in data:
                    if c.get("name") == self._collection:
                        return c.get("id") or c.get("uuid")
        # List all
        r = await client.get(f"http://{self._host}:{self._port}/api/v1/collections")
        if r.status_code == 200:
            for c in r.json():
                if c.get("name") == self._collection:
                    return c.get("id") or c.get("uuid")
        # Create if not exists
        r = await client.post(f"http://{self._host}:{self._port}/api/v1/collections", json={"name": self._collection})
        r.raise_for_status()
        data = r.json()
        return data.get("id") or data.get("uuid")

    async def save_items(self, items: List[RawTrendItem]) -> int:
        """Persist items to ChromaDB via REST."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            col_id = await self._get_collection_id(client)
            documents = []
            metadatas = []
            ids = []
            for it in items:
                doc = it.summary or it.title
                documents.append(doc)
                metadatas.append({
                    "title": it.title,
                    "url": str(it.url) if it.url else None,
                    "source": it.source,
                    "author": it.author,
                    "published_at": it.published_at.isoformat() if it.published_at else None,
                })
                ids.append(f"{it.source}_{uuid.uuid4().hex[:12]}")
            # Provide dummy embeddings to work with Chroma when no embedding function is configured
            embeddings = [[0.0, 0.0, 0.0] for _ in ids]
            payload = {"documents": documents, "metadatas": metadatas, "ids": ids, "embeddings": embeddings}
            r = await client.post(f"http://{self._host}:{self._port}/api/v1/collections/{col_id}/add", json=payload)
            r.raise_for_status()
            return len(ids)

    async def list_candidates(self, limit: int = 200) -> List[Dict[str, Any]]:
        """List recent items from raw_trends to triage, filtering out those already processed.

        Returns dicts: {"id": str, "document": str, "metadata": dict}
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            col_id = await self._get_collection_id(client)
            # Best-effort get; Chroma returns arrays (possibly wrapped in one more array)
            payload: Dict[str, Any] = {"limit": limit}
            r = await client.post(f"http://{self._host}:{self._port}/api/v1/collections/{col_id}/get", json=payload)
            if r.status_code != 200:
                return []
            data = r.json()
            ids = data.get("ids") or []
            docs = data.get("documents") or []
            metas = data.get("metadatas") or []
            # Unwrap if nested
            if ids and isinstance(ids[0], list):
                ids = ids[0]
            if docs and isinstance(docs[0], list):
                docs = docs[0]
            if metas and isinstance(metas[0], list):
                metas = metas[0]
            results: List[Dict[str, Any]] = []
            for i, _id in enumerate(ids):
                meta = metas[i] if i < len(metas) else {}
                status = (meta or {}).get("status")
                if status in ("promoted", "rejected"):
                    continue
                doc = docs[i] if i < len(docs) else None
                results.append({"id": _id, "document": doc, "metadata": meta or {}})
            return results

    async def update_status(self, ids: List[str], status: str) -> bool:
        """Update status metadata for given ids in collection."""
        if not ids:
            return True
        async with httpx.AsyncClient(timeout=10.0) as client:
            col_id = await self._get_collection_id(client)
            metadatas = [{"status": status} for _ in ids]
            payload = {"ids": ids, "metadatas": metadatas}
            r = await client.post(f"http://{self._host}:{self._port}/api/v1/collections/{col_id}/update", json=payload)
            return r.status_code in (200, 204)
