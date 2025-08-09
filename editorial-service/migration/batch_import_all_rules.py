#!/usr/bin/env python3
import json
import os
import time
import urllib.request
from typing import Dict, List, Tuple, Set

BASE = os.getenv("CHROMADB_BASE", "http://localhost:8000/api/v1")
STYLE_COLLECTION = os.getenv("STYLE_COLLECTION", "style_editorial_rules")
PLATFORM_COLLECTION = os.getenv("PLATFORM_COLLECTION", "publication_platform_rules")
BATCH = int(os.getenv("BATCH_SIZE", "128"))

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "output"))
STYLE_FILES = [
    os.path.join(OUTPUT_DIR, "chromadb_rules.json"),
    os.path.join(OUTPUT_DIR, "ai_writing_flow_chromadb_rules.json"),
]
PLATFORM_FILES = [
    os.path.join(OUTPUT_DIR, "publisher_platform_chromadb_rules.json"),
]


def http(method: str, path: str, data: dict | None = None, timeout: float = 30.0):
    url = f"{BASE}{path}"
    body = None
    headers = {"Content-Type": "application/json"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        b = resp.read()
        return json.loads(b.decode("utf-8")) if b else {}


def get_collection_id_by_name(name: str) -> str:
    cols = http("GET", "/collections")
    for c in cols:
        if c.get("name") == name:
            return c["id"]
    # create if missing
    res = http("POST", "/collections", {"name": name})
    return res.get("id")


def load_rules(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all(paths: List[str]) -> List[Dict]:
    docs: List[Dict] = []
    for p in paths:
        if os.path.exists(p):
            docs.extend(load_rules(p))
    return docs


def get_missing_ids(col_id: str, ids: List[str]) -> Set[str]:
    missing: Set[str] = set(ids)
    for i in range(0, len(ids), BATCH):
        chunk = ids[i:i+BATCH]
        res = http("POST", f"/collections/{col_id}/get", {"ids": chunk})
        present = set(res.get("ids", []) or [])
        missing -= present
    return missing


def import_docs(col_id: str, docs: List[Dict]) -> Tuple[int, int]:
    # returns (added, skipped)
    ids = [d["metadata"]["rule_id"] for d in docs]
    missing = get_missing_ids(col_id, ids)
    added = 0
    skipped = len(ids) - len(missing)
    # add only missing
    to_add = [d for d in docs if d["metadata"]["rule_id"] in missing]
    for i in range(0, len(to_add), BATCH):
        chunk = to_add[i:i+BATCH]
        payload = {
            "ids": [d["metadata"]["rule_id"] for d in chunk],
            "documents": [d["content"] for d in chunk],
            "metadatas": [d["metadata"] for d in chunk]
        }
        http("POST", f"/collections/{col_id}/add", payload)
        added += len(chunk)
    return added, skipped


def run_import(name: str, files: List[str], collection: str) -> Dict:
    t0 = time.perf_counter()
    col_id = get_collection_id_by_name(collection)
    docs = load_all(files)
    attempted = len(docs)
    added, skipped = import_docs(col_id, docs)
    elapsed = (time.perf_counter() - t0) * 1000.0
    return {
        "name": name,
        "collection": collection,
        "collection_id": col_id,
        "attempted": attempted,
        "added": added,
        "skipped": skipped,
        "ms": round(elapsed, 2)
    }


def main():
    # style (styleguides + aiwf) into style_editorial_rules
    style_stats = run_import("style", STYLE_FILES, STYLE_COLLECTION)
    # platform into publication_platform_rules
    platform_stats = run_import("platform", PLATFORM_FILES, PLATFORM_COLLECTION)

    ok = style_stats["attempted"] >= 300 and platform_stats["attempted"] >= 100
    print(json.dumps({
        "success": bool(ok),
        "style": style_stats,
        "platform": platform_stats
    }))

if __name__ == "__main__":
    main()
