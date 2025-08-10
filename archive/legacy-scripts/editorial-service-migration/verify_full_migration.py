#!/usr/bin/env python3
import argparse
import json
import os
import random
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Set

# Endpoints
CHROMA_BASE = os.getenv("CHROMADB_BASE", "http://localhost:8000/api/v1")
EDITORIAL_HEALTH = os.getenv("EDITORIAL_HEALTH", "http://localhost:8040/health")

# Collections
STYLE_COLLECTION = os.getenv("STYLE_COLLECTION", "style_editorial_rules")
PLATFORM_COLLECTION = os.getenv("PLATFORM_COLLECTION", "publication_platform_rules")

# Local rule files
OUT_DIR = Path(__file__).resolve().parent / "output"
STYLE_FILES = [
    OUT_DIR / "chromadb_rules.json",
    OUT_DIR / "ai_writing_flow_chromadb_rules.json",
]
PLATFORM_FILES = [
    OUT_DIR / "publisher_platform_chromadb_rules.json",
]

BATCH = int(os.getenv("BATCH_SIZE", "128"))


def http(method: str, url: str, data: dict | None = None, timeout: float = 20.0):
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        b = resp.read()
        return json.loads(b.decode("utf-8")) if b else {}


def get_collection_id_by_name(name: str) -> str:
    cols = http("GET", f"{CHROMA_BASE}/collections")
    for c in cols:
        if c.get("name") == name:
            return c["id"]
    raise RuntimeError(f"Collection not found: {name}")


def load_ids(files: List[Path]) -> List[str]:
    ids: List[str] = []
    for p in files:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            ids.extend([d.get("metadata", {}).get("rule_id") for d in data if isinstance(d, dict)])
    return [i for i in ids if i]


def verify_ids(col_id: str, ids: List[str], sample: int = 50) -> Dict:
    sample_ids = ids.copy()
    random.shuffle(sample_ids)
    sample_ids = sample_ids[: min(sample, len(sample_ids))]
    returned_total = 0
    for i in range(0, len(sample_ids), BATCH):
        chunk = sample_ids[i:i+BATCH]
        res = http("POST", f"{CHROMA_BASE}/collections/{col_id}/get", {"ids": chunk})
        returned = len(res.get("ids", []) or [])
        returned_total += returned
    ok = returned_total == len(sample_ids)
    return {"requested": len(sample_ids), "returned": returned_total, "ok": ok}


def check_editorial_health() -> Dict:
    try:
        health = http("GET", EDITORIAL_HEALTH)
        return {
            "status": (health.get("status") == "healthy"),
            "chromadb": ((health.get("checks", {}).get("chromadb") or {}).get("status") == "healthy"),
        }
    except Exception as e:
        return {"status": False, "chromadb": False, "error": str(e)}


def bench_chroma_rest() -> Dict:
    # Leverage bench_rest_perf.py if available; otherwise skip
    bench = Path(__file__).resolve().parent / "bench_rest_perf.py"
    if not bench.exists():
        return {"skipped": True}
    proc = subprocess.run(["python3", str(bench)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        return {"skipped": True, "error": proc.stderr.strip()}
    try:
        data = json.loads(proc.stdout)
        return data | {"skipped": False}
    except Exception:
        return {"skipped": True, "error": proc.stdout}


def scan_hardcoded(root: Path) -> Dict:
    patterns = ("forbidden_phrases", "required_elements", "style_patterns", "default_rules", "fallback_rules")
    hits = 0
    files = 0
    for p in root.rglob("*.py"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        files += 1
        if any(s in txt for s in patterns):
            hits += 1
    return {"scanned_files": files, "hardcoded_hits": hits, "zero_hardcoded": hits == 0}


def main():
    style_ids = load_ids(STYLE_FILES)
    platform_ids = load_ids(PLATFORM_FILES)

    style_col = get_collection_id_by_name(STYLE_COLLECTION)
    platform_col = get_collection_id_by_name(PLATFORM_COLLECTION)

    style_check = verify_ids(style_col, style_ids, sample=50)
    platform_check = verify_ids(platform_col, platform_ids, sample=50)

    health = check_editorial_health()
    bench = bench_chroma_rest()

    # Scan editorial-service/src for hardcoded patterns
    repo_root = Path(__file__).resolve().parents[2]
    src_dir = repo_root / "editorial-service" / "src"
    hardcoded = scan_hardcoded(src_dir) if src_dir.exists() else {"skipped": True}

    total_rules = len(style_ids) + len(platform_ids)

    success = (
        style_check.get("ok") and platform_check.get("ok") and
        health.get("status") and health.get("chromadb") and
        total_rules >= 355 and hardcoded.get("zero_hardcoded", True)
    )

    print(json.dumps({
        "success": bool(success),
        "totals": {
            "style": len(style_ids),
            "platform": len(platform_ids),
            "overall": total_rules
        },
        "style_check": style_check,
        "platform_check": platform_check,
        "editorial_health": health,
        "perf": bench,
        "hardcoded_scan": hardcoded
    }))

if __name__ == "__main__":
    main()
