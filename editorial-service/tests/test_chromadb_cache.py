import asyncio
import json
import pytest

from src.cache.chromadb_cache import ChromaDBOnlyCache


class FakeRedis:
    def __init__(self):
        self.store = {}
    async def get(self, k):
        return self.store.get(k)
    async def setex(self, k, ttl, v):
        self.store[k] = v
        return True
    async def keys(self, pattern):
        prefix = pattern.rstrip('*')
        return [k for k in self.store.keys() if k.startswith(prefix)]
    async def delete(self, k):
        self.store.pop(k, None)
        return 1


@pytest.mark.asyncio
async def test_cache_store_and_get_only_chromadb():
    r = FakeRedis()
    cache = ChromaDBOnlyCache(r, "style_editorial_rules")

    rules = [
        {"rule_id": "x1", "chromadb_metadata": {"collection_name": "style_editorial_rules", "document_id": "1", "query_timestamp": "t"}},
        {"rule_id": "x2", "chromadb_metadata": {"collection_name": "style_editorial_rules", "document_id": "2"}},  # invalid (missing query_timestamp)
    ]

    stored = await cache.store_rules("q", rules, n_results=5, ttl=10)
    assert stored is True

    fetched = await cache.get_rules("q", n_results=5)
    assert fetched is not None
    assert len(fetched) == 1
    assert fetched[0]["rule_id"] == "x1"
    assert fetched[0]["cache_metadata"]["source"] == "chromadb_cache"


@pytest.mark.asyncio
async def test_cache_stats_and_clear():
    r = FakeRedis()
    cache = ChromaDBOnlyCache(r, "publication_platform_rules")

    await cache.store_rules("a", [{"chromadb_metadata": {"collection_name": "c", "document_id": "1", "query_timestamp": "t"}}])
    await cache.store_rules("b", [{"chromadb_metadata": {"collection_name": "c", "document_id": "2", "query_timestamp": "t"}}])

    s = await cache.stats()
    assert s["collection"] == "publication_platform_rules"
    assert s["cached_keys"] >= 2
    assert s["total_rules"] == s["valid_rules"]
    assert s["all_chromadb_sourced"] is True

    deleted = await cache.clear()
    assert deleted >= 2

    s2 = await cache.stats()
    assert s2["cached_keys"] == 0
