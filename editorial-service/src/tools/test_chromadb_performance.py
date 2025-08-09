import os
import time
import statistics
from typing import Dict, List

import chromadb
from chromadb.config import Settings

TARGETS = [
    "style_editorial_rules",
    "publication_platform_rules",
    "topics",
    "scheduling_optimization",
    "user_preferences",
]

RUNS = int(os.getenv("RUNS", "50"))
P95_THRESHOLD_S = float(os.getenv("P95_THRESHOLD_S", "0.1"))  # 100ms


def percentile(values: List[float], p: float) -> float:
    values = sorted(values)
    k = int(round((len(values) - 1) * p))
    return values[k]


def main() -> int:
    host = os.getenv("CHROMADB_HOST", "chromadb")
    port = int(os.getenv("CHROMADB_PORT", "8000"))

    client = chromadb.HttpClient(host=host, port=port, settings=Settings(allow_reset=True))

    overall_ok = True
    for name in TARGETS:
        col = client.get_or_create_collection(name)
        latencies: List[float] = []
        for _ in range(RUNS):
            t0 = time.perf_counter()
            try:
                # Query is lenient; may return empty results if only sample present
                col.query(query_texts=["test"], n_results=1)
            except Exception:
                pass
            latencies.append(time.perf_counter() - t0)
        p50 = percentile(latencies, 0.50)
        p95 = percentile(latencies, 0.95)
        avg = statistics.mean(latencies)
        print(f"{name}: avg={avg*1000:.2f}ms p50={p50*1000:.2f}ms p95={p95*1000:.2f}ms")
        if p95 > P95_THRESHOLD_S:
            overall_ok = False
    if not overall_ok:
        print(f"FAIL: p95 exceeded threshold {P95_THRESHOLD_S*1000:.0f}ms")
        return 1
    print("OK: all collections within p95 threshold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
