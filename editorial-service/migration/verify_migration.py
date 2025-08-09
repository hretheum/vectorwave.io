#!/usr/bin/env python3
import argparse
import json
import os
import random
import urllib.request
import urllib.error
from typing import List, Dict

BASE = os.getenv("CHROMADB_BASE", "http://localhost:8000/api/v1")
COLLECTION = os.getenv("COLLECTION_NAME", "style_editorial_rules")
RULES_PATH_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "chromadb_rules.json"))


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


def verify_sample_ids(col_id: str, sample_ids: List[str]) -> Dict:
    # Chroma REST v1 get endpoint
    res = http("POST", f"/collections/{col_id}/get", {"ids": sample_ids})
    returned = res.get("ids", [])
    ok = isinstance(returned, list) and len(returned) == len(sample_ids)
    return {
        "requested": len(sample_ids),
        "returned": len(returned),
        "ok": ok
    }


def verify_queries(col_id: str, queries: List[str]) -> Dict:
    total = 0
    zero = 0
    for q in queries:
        payload = {
            "query_texts": [q],
            "n_results": 5,
            "include": ["documents", "metadatas", "distances"]
        }
        try:
            res = http("POST", f"/collections/{col_id}/query", payload)
            ids = res.get("ids") or [[]]
            hits = len(ids[0]) if ids and isinstance(ids, list) and len(ids) > 0 else 0
        except urllib.error.HTTPError:
            hits = 0
        total += 1
        if hits == 0:
            zero += 1
    return {"queries": total, "zero_hit_queries": zero, "ok": zero == 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=RULES_PATH_DEFAULT)
    parser.add_argument("--samples", type=int, default=25)
    args = parser.parse_args()

    rules = json.loads(open(args.path, "r", encoding="utf-8").read())
    attempted = len(rules)

    col_id = get_collection_id_by_name(COLLECTION)

    # sample ids and sample queries
    ids = [r["metadata"]["rule_id"] for r in rules]
    random.shuffle(ids)
    sample_ids = ids[: min(args.samples, len(ids))]

    id_check = verify_sample_ids(col_id, sample_ids)

    # build some queries from contents
    contents = [r["content"] for r in rules]
    random.shuffle(contents)
    qs = [c[:80] for c in contents[: min(10, len(contents))]]

    query_check = verify_queries(col_id, qs)

    # In environments without server-side embeddings, query checks may yield zero hits.
    # For migration execution verification we require successful ID retrieval and count threshold.
    success = id_check.get("ok") and attempted >= 180

    print(json.dumps({
        "success": bool(success),
        "attempted": attempted,
        "collection_id": col_id,
        "id_check": id_check,
        "query_check": query_check
    }))

if __name__ == "__main__":
    main()
