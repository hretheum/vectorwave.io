#!/usr/bin/env python3
import json
import os
import random
import urllib.request
from typing import List

BASE = os.getenv("CHROMADB_BASE", "http://localhost:8000/api/v1")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "publication_platform_rules")
INPUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "publisher_platform_chromadb_rules.json"))


def http(method: str, path: str, data: dict | None = None):
    url = f"{BASE}{path}"
    body = None
    headers = {"Content-Type": "application/json"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        b = resp.read()
        return json.loads(b.decode("utf-8")) if b else {}


def get_collection_id_by_name(name: str) -> str:
    cols = http("GET", "/collections")
    for c in cols:
        if c.get("name") == name:
            return c["id"]
    raise RuntimeError(f"Collection not found: {name}")


def verify_ids(col_id: str, sample_ids: List[str]) -> dict:
    res = http("POST", f"/collections/{col_id}/get", {"ids": sample_ids})
    returned = res.get("ids", [])
    return {"requested": len(sample_ids), "returned": len(returned), "ok": len(returned) == len(sample_ids)}


def main():
    rules = json.loads(open(INPUT, "r", encoding="utf-8").read())
    ids = [r["metadata"]["rule_id"] for r in rules]
    random.shuffle(ids)
    sample = ids[:25]

    col_id = get_collection_id_by_name(COLLECTION_NAME)
    id_check = verify_ids(col_id, sample)
    success = id_check.get("ok") and len(ids) >= 100

    print(json.dumps({
        "success": bool(success),
        "collection_id": col_id,
        "total": len(ids),
        "id_check": id_check
    }))

if __name__ == "__main__":
    main()
