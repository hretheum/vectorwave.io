#!/usr/bin/env python3
import json
import os
import urllib.request
from typing import Dict, List

CHROMA_BASE = os.getenv("CHROMADB_BASE", "http://localhost:8000/api/v1")
EDITORIAL_HEALTH = os.getenv("EDITORIAL_HEALTH", "http://localhost:8040/health")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "publication_platform_rules")
RULES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "publisher_platform_chromadb_rules.json"))
TARGET_PLATFORMS = ["linkedin", "twitter", "substack", "beehiiv", "ghost"]


def http(method: str, url: str, data: dict | None = None, timeout: float = 15.0):
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        b = resp.read()
        return json.loads(b.decode("utf-8")) if b else {}


def get_collection_id_by_name(name: str) -> str:
    cols = http("GET", f"{CHROMA_BASE}/collections")
    for c in cols:
        if c.get("name") == name:
            return c["id"]
    raise RuntimeError(f"Collection not found: {name}")


def verify_all_ids(col_id: str, ids: List[str], batch: int = 128) -> Dict:
    total = len(ids)
    returned = 0
    for i in range(0, total, batch):
        chunk = ids[i:i+batch]
        res = http("POST", f"{CHROMA_BASE}/collections/{col_id}/get", {"ids": chunk})
        rids = res.get("ids", [])
        returned += len(rids)
    return {"total": total, "returned": returned, "ok": returned == total}


def verify_editorial_health() -> Dict:
    health = http("GET", EDITORIAL_HEALTH, None, timeout=5.0)
    return {
        "status": health.get("status") == "healthy",
        "chromadb": ((health.get("checks", {}).get("chromadb") or {}).get("status") == "healthy")
    }


def count_platforms_local(rules: List[Dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in rules:
        p = (r.get("metadata", {}).get("platform") or "universal").lower()
        counts[p] = counts.get(p, 0) + 1
    return counts


def main():
    rules = json.loads(open(RULES_PATH, "r", encoding="utf-8").read())
    ids = [r["metadata"]["rule_id"] for r in rules]

    col_id = get_collection_id_by_name(COLLECTION_NAME)
    id_check = verify_all_ids(col_id, ids)

    health = verify_editorial_health()

    platform_counts = count_platforms_local(rules)
    platforms_ok = all(platform_counts.get(p, 0) > 0 for p in TARGET_PLATFORMS)

    success = id_check.get("ok") and health.get("status") and health.get("chromadb") and platforms_ok

    print(json.dumps({
        "success": bool(success),
        "collection": COLLECTION_NAME,
        "collection_id": col_id,
        "ids": id_check,
        "editorial_health": health,
        "platform_counts": platform_counts,
        "platforms_ok": platforms_ok
    }))

if __name__ == "__main__":
    main()
