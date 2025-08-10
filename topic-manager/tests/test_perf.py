import sys, pathlib, time
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from matching import suggest_platforms


def test_perf_p95_under_10ms():
    topics = [
        {"title": f"AI trend {i}", "keywords": ["AI", "dev"]} for i in range(50)
    ]
    topics += [
        {"title": f"Enterprise case {i}", "keywords": ["B2B", "case study"]} for i in range(50)
    ]

    latencies = []
    for t in topics:
        start = time.perf_counter()
        _ = suggest_platforms(t)
        latencies.append((time.perf_counter() - start) * 1000.0)

    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95) - 1]
    assert p95 < 10.0
