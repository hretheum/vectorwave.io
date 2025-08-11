#!/usr/bin/env python3
import sys
import json
import os
import urllib.request
import urllib.error

CHROMA_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMADB_PORT", "8000"))


def http_get(path):
    url = f"http://{CHROMA_HOST}:{CHROMA_PORT}{path}"
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)


def http_post(path, payload):
    url = f"http://{CHROMA_HOST}:{CHROMA_PORT}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def get_collection_id(name):
    cols = http_get("/api/v1/collections")
    if isinstance(cols, list):
        for c in cols:
            if c.get("name") == name:
                return c.get("id") or c.get("uuid")
    # Some versions allow name filter
    try:
        c = http_get(f"/api/v1/collections?name={name}")
        if isinstance(c, dict) and c.get("id"):
            return c.get("id")
    except Exception:
        pass
    raise SystemExit(f"Collection not found: {name}")


def main():
    # Args: --collection NAME --where JSON --min-count N
    args = sys.argv[1:]
    coll = None
    where = {}
    min_count = 1
    i = 0
    while i < len(args):
        if args[i] == "--collection":
            i += 1
            coll = args[i]
        elif args[i] == "--where":
            i += 1
            where = json.loads(args[i])
        elif args[i] == "--min-count":
            i += 1
            min_count = int(args[i])
        elif args[i] in ("--host", "--port"):
            # Optional override
            if args[i] == "--host":
                i += 1
                globals()["CHROMA_HOST"] = args[i]
            else:
                i += 1
                globals()["CHROMA_PORT"] = int(args[i])
        else:
            raise SystemExit(f"Unknown arg: {args[i]}")
        i += 1

    if not coll:
        raise SystemExit("--collection required")

    col_id = get_collection_id(coll)
    resp = http_post(f"/api/v1/collections/{col_id}/get", {"where": where, "include": ["metadatas"]})
    ids = resp.get("ids") or []
    # Some versions structure ids as list of lists
    if ids and isinstance(ids[0], list):
        total = sum(len(x) for x in ids)
    else:
        total = len(ids)

    print(json.dumps({
        "host": CHROMA_HOST,
        "port": CHROMA_PORT,
        "collection": coll,
        "where": where,
        "count": total,
        "min_count": min_count,
        "ok": total >= min_count
    }))

    if total < min_count:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
