from __future__ import annotations
import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class ChromaDBOnlyCache:
    """
    Cache for ChromaDB-sourced rules only.

    Stores JSON-serialized rule lists per (query, n_results) key and rejects entries
    that do not contain valid 'chromadb_metadata'.
    """

    def __init__(self, redis_client: Any, collection_name: str) -> None:
        self.redis = redis_client
        self.collection_name = collection_name
        self.cache_prefix = f"chromadb_cache:{collection_name}"

    def _make_key(self, query: str, n_results: int) -> str:
        return f"{self.cache_prefix}:{hash((query, n_results))}"

    def _has_valid_chromadb_metadata(self, rule: Dict[str, Any]) -> bool:
        md = rule.get("chromadb_metadata", {})
        required = ("collection_name", "document_id", "query_timestamp")
        return isinstance(md, dict) and all(k in md for k in required)

    async def get_rules(self, query: str, n_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        key = self._make_key(query, n_results)
        raw = await self.redis.get(key)
        if not raw:
            return None
        try:
            rules = json.loads(raw)
        except Exception:
            return None
        valid = [r for r in rules if self._has_valid_chromadb_metadata(r)]
        return valid or None

    async def store_rules(self, query: str, rules: List[Dict[str, Any]], n_results: int = 10, ttl: int = 3600) -> bool:
        valid_rules: List[Dict[str, Any]] = []
        now_iso = datetime.utcnow().isoformat() + "Z"
        for r in rules:
            if not self._has_valid_chromadb_metadata(r):
                continue
            r.setdefault("cache_metadata", {})
            r["cache_metadata"].update({
                "cached_at": now_iso,
                "ttl": ttl,
                "source": "chromadb_cache"
            })
            valid_rules.append(r)
        if not valid_rules:
            return False
        key = self._make_key(query, n_results)
        await self.redis.setex(key, ttl, json.dumps(valid_rules, default=str))
        return True

    async def clear(self) -> int:
        pattern = f"{self.cache_prefix}:*"
        keys = await self.redis.keys(pattern)
        deleted = 0
        for k in keys or []:
            try:
                await self.redis.delete(k)
                deleted += 1
            except Exception:
                pass
        return deleted

    async def stats(self) -> Dict[str, Any]:
        pattern = f"{self.cache_prefix}:*"
        keys = await self.redis.keys(pattern)
        total_rules = 0
        valid_rules = 0
        for k in keys or []:
            raw = await self.redis.get(k)
            if not raw:
                continue
            try:
                rules = json.loads(raw)
            except Exception:
                continue
            total_rules += len(rules)
            valid_rules += len([r for r in rules if self._has_valid_chromadb_metadata(r)])
        return {
            "collection": self.collection_name,
            "cached_keys": len(keys or []),
            "total_rules": total_rules,
            "valid_rules": valid_rules,
            "validity_rate": (valid_rules / total_rules) if total_rules else 0.0,
            "all_chromadb_sourced": total_rules > 0 and valid_rules == total_rules
        }
