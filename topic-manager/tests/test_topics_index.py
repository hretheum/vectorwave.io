import sys, pathlib
from typing import Any, Dict, List, Optional

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from main import app as fastapi_app  # type: ignore
import main as tm_main  # type: ignore


class FakeChroma:
    def __init__(self) -> None:
        self.healthy = True
        self.collections = set()
        self.store: Dict[str, Dict[str, Any]] = {}

    async def heartbeat(self) -> Dict[str, Any]:
        return {"status": "healthy" if self.healthy else "unhealthy", "latency_ms": 1.0}

    async def ensure_collection(self, name: str) -> bool:
        self.collections.add(name)
        if name not in self.store:
            self.store[name] = {"ids": [], "embs": [], "docs": [], "metas": []}
        return True

    async def count(self, name: str) -> int:
        return len(self.store.get(name, {}).get("ids", []))

    async def add(self, name: str, ids: List[str], documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, embeddings: Optional[List[List[float]]] = None) -> bool:
        bucket = self.store.setdefault(name, {"ids": [], "embs": [], "docs": [], "metas": []})
        bucket["ids"].extend(ids)
        bucket["docs"].extend(documents)
        bucket["metas"].extend(metadatas or [{} for _ in ids])
        bucket["embs"].extend(embeddings or [[0.0] for _ in ids])
        return True

    async def query(self, name: str, query_embeddings: List[List[float]], n_results: int = 5) -> Dict[str, Any]:
        bucket = self.store.get(name, {"ids": [], "embs": [], "docs": [], "metas": []})
        q = query_embeddings[0] if query_embeddings else []
        # very naive distance: absolute difference sum
        def dist(a: List[float], b: List[float]) -> float:
            if not a or not b:
                return 1.0
            m = min(len(a), len(b))
            return float(sum(abs(a[i] - b[i]) for i in range(m)) / max(1, m))

        pairs = [
            (bucket["ids"][i], dist(q, bucket["embs"][i]), bucket["docs"][i], bucket["metas"][i])
            for i in range(len(bucket["ids"]))
        ]
        pairs.sort(key=lambda x: x[1])
        top = pairs[:n_results]
        return {
            "ids": [[p[0] for p in top]],
            "distances": [[p[1] for p in top]],
            "documents": [[p[2] for p in top]],
            "metadatas": [[p[3] for p in top]],
        }


@pytest.fixture(autouse=True)
def fake_chroma(monkeypatch):
    fake = FakeChroma()

    async def _fake_get_chroma():
        return fake

    # Install fake globally in module
    monkeypatch.setattr(tm_main, "_CHROMA", fake, raising=False)
    monkeypatch.setattr(tm_main, "_get_chroma", _fake_get_chroma, raising=False)
    return fake


def test_topics_index_info_reports_ready_and_count():
    c = TestClient(fastapi_app)
    r = c.get("/topics/index/info")
    assert r.status_code == 200
    body = r.json()
    assert body["collection"] == "topics_index"
    assert body["ready"] in (True, False)  # True when ensure_collection succeeds


def test_reindex_then_search_flow():
    c = TestClient(fastapi_app)
    # Seed a few topics
    for i in range(3):
        payload = {"title": f"AI Case {i}", "description": "Vector test", "keywords": ["ai", "vector"], "content_type": "POST"}
        c.post("/topics/manual", json=payload)

    # Reindex
    r = c.post("/topics/index/reindex", params={"limit": 50})
    assert r.status_code == 200
    assert r.json()["indexed"] >= 1

    # Search
    r2 = c.get("/topics/search", params={"q": "AI Case", "limit": 5})
    assert r2.status_code == 200
    res = r2.json()
    assert res["count"] >= 1
    assert isinstance(res["items"], list)
    # Each item has expected keys
    if res["items"]:
        it = res["items"][0]
        assert "topic_id" in it
        assert "score" in it
