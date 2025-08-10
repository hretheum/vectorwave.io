#!/usr/bin/env python3
import json
import os
import time
import urllib.request
import urllib.error
from typing import List, Dict

CHROMA_BASE = os.getenv("CHROMADB_BASE", "http://localhost:8000/api/v1")
EDITORIAL_HEALTH = os.getenv("EDITORIAL_HEALTH", "http://localhost:8040/health")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "style_editorial_rules")
AIWF_RULES = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "ai_writing_flow_chromadb_rules.json"))


def http(method: str, url: str, data: dict | None = None, timeout: float = 15.0):
    body = None
    headers = {"Content-Type": "application/json"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
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
    status = health.get("status") == "healthy"
    chroma_status = ((health.get("checks", {}).get("chromadb") or {}).get("status") == "healthy")
    return {"status": status, "chromadb": chroma_status}


def main():
    # Load AIWF ids
    rules = json.loads(open(AIWF_RULES, "r", encoding="utf-8").read())
    ids = [r["metadata"]["rule_id"] for r in rules]

    # Verify presence in collection
    col_id = get_collection_id_by_name(COLLECTION_NAME)
    id_check = verify_all_ids(col_id, ids)

    # Editorial health
    health = verify_editorial_health()

    success = id_check.get("ok") and health.get("status") and health.get("chromadb")

    print(json.dumps({
        "success": bool(success),
        "collection": COLLECTION_NAME,
        "collection_id": col_id,
        "ids": id_check,
        "editorial_health": health
    }))

if __name__ == "__main__":
    main()
