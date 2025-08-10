#!/usr/bin/env python3
import json
import os
import sys
import time
from typing import List, Dict
import urllib.request
import urllib.error

BASE = os.getenv("CHROMADB_BASE", "http://localhost:8000/api/v1")
COLLECTION = os.getenv("COLLECTION_NAME", "style_editorial_rules")
INPUT = os.getenv("RULES_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "chromadb_rules.json")))
BATCH = int(os.getenv("BATCH_SIZE", "128"))


def http(method: str, path: str, data: dict | None = None):
    url = f"{BASE}{path}"
    body = None
    headers = {"Content-Type": "application/json"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            b = resp.read()
            return json.loads(b.decode("utf-8")) if b else {}
    except urllib.error.HTTPError as e:
        try:
            payload = e.read().decode("utf-8")
        except Exception:
            payload = str(e)
        raise RuntimeError(f"HTTP {e.code} {url}: {payload}")


def ensure_collection(name: str):
    # idempotent create
    try:
        http("POST", "/collections", {"name": name})
    except Exception:
        pass


def load_rules(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def migrate(path: str, name: str) -> Dict:
    rules = load_rules(path)
    ensure_collection(name)

    total = len(rules)
    added = 0

    for i in range(0, total, BATCH):
        chunk = rules[i:i+BATCH]
        ids = [r["metadata"]["rule_id"] for r in chunk]
        documents = [r["content"] for r in chunk]
        metadatas = [r["metadata"] for r in chunk]
        http("POST", f"/collections/{name}/add", {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas
        })
        added += len(chunk)

    return {"attempted": total, "added": added}


def main():
    result = migrate(INPUT, COLLECTION)
    print(json.dumps({
        "status": "ok",
        "collection": COLLECTION,
        "attempted": result["attempted"],
        "added": result["added"]
    }))

if __name__ == "__main__":
    main()
