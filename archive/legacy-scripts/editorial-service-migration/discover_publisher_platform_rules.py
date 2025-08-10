#!/usr/bin/env python3
import argparse
import json
import os
import re
from typing import Dict, List, Any, Tuple

PUBLISHER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "publisher"))
OUTPUT_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "publisher_platform_rules_catalog.json"))

PLATFORMS = ["linkedin", "twitter", "substack", "beehiiv", "ghost", "youtube"]

PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("max_length", re.compile(r"max[_\- ]?length\s*[:=]\s*(\d+)", re.IGNORECASE)),
    ("character_limit", re.compile(r"character(s)?\s*limit\s*[:=]\s*(\d+)", re.IGNORECASE)),
    ("hashtag_rules", re.compile(r"hashtag[s]?\s*(rules|limit|count)\s*[:=]?\s*(\d+)?", re.IGNORECASE)),
    ("platform_specific", re.compile(r"linkedin|twitter|substack|beehiiv|ghost|youtube", re.IGNORECASE)),
    ("forbidden_phrases", re.compile(r"forbidden|avoid|prohibit|never", re.IGNORECASE)),
    ("required_elements", re.compile(r"require(d)?|must|include", re.IGNORECASE)),
    ("regex_pattern", re.compile(r"re\.compile\(.*\)", re.IGNORECASE)),
]

VALUE_STRING = re.compile(r"['\"]([^'\"]{2,})['\"]")
DIGITS = re.compile(r"(\d+)")


def extract_values(snippet: str) -> Dict[str, Any]:
    values = VALUE_STRING.findall(snippet)
    nums = DIGITS.findall(snippet)
    return {"strings": values[:10], "numbers": [int(n) for n in nums[:10]]}


def classify_platform(text: str, file_path: str) -> str:
    t = text.lower() + " " + file_path.lower()
    for p in PLATFORMS:
        if p in t:
            return p
    return "universal"


def scan_file(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return {"file": path, "exists": False, "hits": []}

    hits: List[Dict[str, Any]] = []
    lines = content.splitlines()
    for idx, line in enumerate(lines, start=1):
        for name, rx in PATTERNS:
            if rx.search(line):
                start = max(1, idx - 2)
                end = min(len(lines), idx + 2)
                snippet = "\n".join(lines[start-1:end])
                values = extract_values(snippet)
                hits.append({
                    "type": name,
                    "platform": classify_platform(snippet, path),
                    "line": idx,
                    "snippet": snippet,
                    "values": values
                })
                break
    return {"file": path, "exists": True, "hits": hits}


def scan_publisher(root: str) -> Dict[str, Any]:
    catalog = {"files": [], "total_hits": 0}
    include_ext = (".py", ".js", ".md", ".yml", ".yaml", ".json")
    for r, _dirs, files in os.walk(root):
        for fname in files:
            if not fname.endswith(include_ext):
                continue
            path = os.path.join(r, fname)
            entry = scan_file(path)
            catalog["files"].append(entry)
            catalog["total_hits"] += len(entry.get("hits", []))
    return catalog


def main():
    parser = argparse.ArgumentParser(description="Discover platform-specific rules in publisher module")
    parser.add_argument("--root", default=PUBLISHER_DIR)
    parser.add_argument("--output", default=OUTPUT_DEFAULT)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    catalog = scan_publisher(args.root)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(json.dumps({"status": "ok", "output": args.output, "files": len(catalog["files"]), "total_hits": catalog["total_hits"]}))


if __name__ == "__main__":
    main()
