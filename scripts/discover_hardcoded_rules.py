import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any

# Files to scan (from roadmap)
CANDIDATE_PATHS = [
    "kolegium/ai_writing_flow/src/ai_writing_flow/crews/style_crew.py",
    "kolegium/ai_writing_flow/src/ai_writing_flow/tools/styleguide_loader.py",
    "kolegium/ai_writing_flow/src/ai_writing_flow/style_linear.py",
]

PATTERNS = {
    "forbidden_phrases": re.compile(r"forbidden_phrases\s*=\s*\[(?P<body>.*?)\]", re.DOTALL),
    "required_elements": re.compile(r"required_elements\s*=\s*\{(?P<body>.*?)\}", re.DOTALL),
    "style_patterns": re.compile(r"style_patterns\s*=\s*\[(?P<body>.*?)\]", re.DOTALL),
}

STRING_RE = re.compile(r"([\"'])(?P<val>.*?)(?<!\\)\1")


def extract_strings(body: str) -> List[str]:
    return [m.group("val") for m in STRING_RE.finditer(body)]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return ""


def scan_file(path: Path) -> Dict[str, Any]:
    content = read_text(path)
    results: Dict[str, Any] = {"file": str(path), "hits": []}
    for key, rx in PATTERNS.items():
        for match in rx.finditer(content):
            body = match.group("body")
            values = extract_strings(body)
            results["hits"].append({
                "type": key,
                "count": len(values),
                "snippet": body[:200] + ("..." if len(body) > 200 else ""),
                "values_preview": values[:10],
            })
    return results


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "editorial-service" / "migration" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = out_dir / "rules_catalog.json"

    catalog: Dict[str, Any] = {"files": [], "total_hits": 0}

    for rel in CANDIDATE_PATHS:
        p = repo_root / rel
        if not p.exists():
            catalog["files"].append({"file": str(p), "exists": False, "hits": []})
            continue
        res = scan_file(p)
        res["exists"] = True
        total = sum(h["count"] for h in res["hits"])
        catalog["total_hits"] += total
        catalog["files"].append(res)

    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    print(f"catalog written: {catalog_path}")
    print(f"total_hits={catalog['total_hits']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
