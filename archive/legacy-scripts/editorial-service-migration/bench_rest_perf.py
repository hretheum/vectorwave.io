#!/usr/bin/env python3
import json
import time
import random
import string
import urllib.request
import urllib.error

BASE = "http://localhost:8000/api/v1"


def http(method: str, path: str, data: dict | None = None):
    url = f"{BASE}{path}"
    body = None
    headers = {"Content-Type": "application/json"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            b = resp.read()
            if b:
                return json.loads(b.decode("utf-8"))
            return {}
    except urllib.error.HTTPError as e:
        # Return error payload if exists
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"error": str(e)}


def ensure_base_collection():
    http("POST", "/collections", {
        "name": "style_editorial_rules",
        "metadata": {"schema_version": 1, "description": "Content style and editorial validation rules"}
    })


def recreate_perf_collection(name: str):
    http("DELETE", f"/collections/{name}")
    http("POST", "/collections", {"name": name})


def gen_docs(n: int):
    ids = [f"perf_{i:04d}" for i in range(n)]
    documents = [
        "Rule perf sample %d: " % i + " ".join(
            "".join(random.choice(string.ascii_lowercase) for _ in range(8)) for _ in range(20)
        ) for i in range(n)
    ]
    metadatas = [{"rule_id": ids[i], "rule_type": "style", "platform": "universal"} for i in range(n)]
    return ids, documents, metadatas


def add_docs(name: str, ids, documents, metadatas):
    http("POST", f"/collections/{name}/add", {
        "ids": ids,
        "documents": documents,
        "metadatas": metadatas
    })


def query_once(name: str, q: str):
    return http("POST", f"/collections/{name}/query", {
        "query_texts": [q],
        "n_results": 5
    })


def main():
    ensure_base_collection()
    test_col = "style_editorial_rules_testperf"
    recreate_perf_collection(test_col)

    ids, docs, metas = gen_docs(200)
    add_docs(test_col, ids, docs, metas)

    # warmup
    query_once(test_col, "test")

    times = []
    for i in range(100):
        q = docs[i % len(docs)][:80]
        t0 = time.perf_counter()
        _ = query_once(test_col, q)
        dt = time.perf_counter() - t0
        times.append(dt)
        time.sleep(0.01)

    times.sort()
    N = len(times)
    def pct(p):
        k = int((p*N)/100)
        if k >= N:
            k = N-1
        return times[k]

    result = {
        "queries": N,
        "p50_ms": round(pct(50)*1000, 2),
        "p95_ms": round(pct(95)*1000, 2),
        "p99_ms": round(pct(99)*1000, 2)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
