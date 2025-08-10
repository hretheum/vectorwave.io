#!/usr/bin/env python3
import json
import os
import urllib.request
from typing import List, Dict

BASE = os.getenv("CHROMADB_BASE", "http://localhost:8000/api/v1")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "publication_platform_rules")
INPUT = os.getenv("RULES_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "publisher_platform_chromadb_rules.json")))
BATCH = int(os.getenv("BATCH_SIZE", "128"))


def http(method: str, path: str, data: dict | None = None):
    url = f"{BASE}{path}"
    body = None
    headers = {"Content-Type": "application/json"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
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


def migrate(path: str, collection_name: str) -> Dict:
    rules = load_rules(path)
    col_id = get_collection_id_by_name(collection_name)

    total = len(rules)
    added = 0

    for i in range(0, total, BATCH):
        chunk = rules[i:i+BATCH]
        payload = {
            "ids": [r["metadata"]["rule_id"] for r in chunk],
            "documents": [r["content"] for r in chunk],
            "metadatas": [r["metadata"] for r in chunk]
        }
        http("POST", f"/collections/{col_id}/add", payload)
        added += len(chunk)

    return {"attempted": total, "added": added, "collection_id": col_id}


def main():
    result = migrate(INPUT, COLLECTION_NAME)
    print(json.dumps({"status": "ok", **result}))

if __name__ == "__main__":
    main()
