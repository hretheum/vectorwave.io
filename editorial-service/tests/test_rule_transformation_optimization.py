import json
from pathlib import Path
import time

try:
    from migration.optimized_transformation import transform_aiwf_catalog_fast, transform_platform_catalog_fast  # type: ignore
except Exception:  # pragma: no cover
    transform_aiwf_catalog_fast = None  # type: ignore
    transform_platform_catalog_fast = None  # type: no cover


def test_optimized_aiwf_speed():
    if transform_aiwf_catalog_fast is None:
        return
    # Prepare synthetic large catalog
    files = []
    for i in range(50):
        hits = []
        # 10 hits per file (5 with values, 5 directives)
        for j in range(5):
            hits.append({
                "type": "forbidden_phrases",
                "snippet": f"forbidden_phrases = ['foo{i}{j}', 'bar{i}{j}']",
                "values_preview": [f"foo{i}{j}", f"bar{i}{j}"],
                "priority_guess": "high",
                "category_guess": "forbidden"
            })
            hits.append({
                "type": "directive_line",
                "snippet": "You should avoid passive voice.",
                "values_preview": [],
                "priority_guess": "medium",
                "category_guess": "directive_line"
            })
        files.append({"file": f"/tmp/f{i}.py", "hits": hits})

    catalog = {"files": files}
    t0 = time.perf_counter()
    docs = transform_aiwf_catalog_fast(catalog, workers=8)
    elapsed = (time.perf_counter() - t0) * 1000.0
    # Expect hundreds of docs generated quickly
    assert len(docs) > 200
    assert elapsed < 5000  # <5s for synthetic workload


def test_optimized_platform_speed():
    if transform_platform_catalog_fast is None:
        return
    # Prepare synthetic platform catalog
    files = []
    for i in range(50):
        hits = []
        for j in range(5):
            hits.append({
                "type": "max_length",
                "platform": "linkedin",
                "line": j,
                "snippet": f"MAX_LENGTH = {300 + j}",
                "values": {"strings": ["linkedin"], "numbers": [300 + j]}
            })
            hits.append({
                "type": "forbidden_phrases",
                "platform": "twitter",
                "line": j,
                "snippet": "Avoid 'salesy' wording",
                "values": {"strings": [f"salesy{j}"], "numbers": []}
            })
        files.append({"file": f"/tmp/p{i}.py", "hits": hits})

    catalog = {"files": files}
    t0 = time.perf_counter()
    docs = transform_platform_catalog_fast(catalog, workers=8)
    elapsed = (time.perf_counter() - t0) * 1000.0
    assert len(docs) > 200
    assert elapsed < 5000
