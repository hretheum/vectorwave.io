#!/usr/bin/env python3
import argparse
import json
import os
import random
import statistics
import string
import time
from typing import List

import chromadb
from chromadb.config import Settings

DEFAULT_COLLECTION = os.getenv("COLLECTION_NAME", "style_editorial_rules_testperf")
CHROMA_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMADB_PORT", "8000"))


def random_text(n: int = 10) -> str:
    return " ".join(
        "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 10)))
        for _ in range(n)
    )


def run_benchmark(collection_name: str = DEFAULT_COLLECTION, docs: int = 200, queries: int = 100) -> dict:
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, settings=Settings(allow_reset=True))

    # Create or reset collection
    try:
        col = client.get_collection(collection_name)
        try:
            col.delete(where={})
        except Exception:
            pass
    except Exception:
        col = client.create_collection(collection_name)

    # Insert sample docs
    ids = [f"perf_{i:04d}" for i in range(docs)]
    documents = [f"Rule perf sample {i}: {random_text(20)}" for i in range(docs)]
    metadatas = [{"rule_id": ids[i], "rule_type": "style", "platform": "universal"} for i in range(docs)]

    BATCH = 128
    for i in range(0, docs, BATCH):
        s = slice(i, i + BATCH)
        col.add(ids=ids[s], documents=documents[s], metadatas=metadatas[s])

    # Warmup
    _ = col.query(query_texts=["test"], n_results=5)

    # Benchmark queries
    times: List[float] = []
    for _ in range(queries):
        q = random.choice(documents)[:80]
        t0 = time.perf_counter()
        _ = col.query(query_texts=[q], n_results=5)
        dt = (time.perf_counter() - t0)
        times.append(dt)

    p95 = statistics.quantiles(times, n=100)[94]
    p99 = statistics.quantiles(times, n=100)[98]

    result = {
        "docs": docs,
        "queries": queries,
        "p50_ms": round(statistics.median(times) * 1000, 2),
        "p95_ms": round(p95 * 1000, 2),
        "p99_ms": round(p99 * 1000, 2),
    }
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--docs", type=int, default=200)
    parser.add_argument("--queries", type=int, default=100)
    args = parser.parse_args()

    run_benchmark(args.collection, args.docs, args.queries)
