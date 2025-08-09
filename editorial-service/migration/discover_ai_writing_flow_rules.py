#!/usr/bin/env python3
import argparse
import json
import os
import re
from typing import Dict, List, Any, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "kolegium", "ai_writing_flow"))
OUTPUT_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "ai_writing_flow_rules_catalog.json"))

RULE_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("forbidden_phrases", re.compile(r"\bforbidden_phrases\s*=\s*\[")),
    ("required_elements", re.compile(r"\brequired_elements\s*=\s*\{")),
    ("style_patterns", re.compile(r"\bstyle_patterns\s*=\s*\[")),
    ("regex_compile", re.compile(r"re\.compile\(.*\)")),
]

VALUE_STRING = re.compile(r"['\"]([^'\"]{2,})['\"]")

PRIORITY_MAP: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(must|required|never|forbid|prohibit)\b", re.IGNORECASE), "high"),
    (re.compile(r"\b(should|avoid|limit)\b", re.IGNORECASE), "medium"),
]

CATEGORY_MAP: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"forbidden|avoid|prohibit|never", re.IGNORECASE), "forbidden"),
    (re.compile(r"require|must|include", re.IGNORECASE), "required"),
    (re.compile(r"pattern|regex|compile", re.IGNORECASE), "pattern"),
]

INTEGRATION_HINTS = [re.compile(p, re.IGNORECASE) for p in [
    "editorial", "validate_selective", "validate_comprehensive", "client", "http", "chromadb"
]]

FILE_INCLUDE_DIRS = [
    os.path.join(ROOT, "src", "ai_writing_flow"),
    os.path.join(ROOT, "deployment", "backups"),
]


def infer_priority(text: str) -> str:
    for rx, p in PRIORITY_MAP:
        if rx.search(text):
            return p
    return "low"


def infer_category(text: str, rule_type_hint: str) -> str:
    for rx, c in CATEGORY_MAP:
        if rx.search(text):
            return c
    if rule_type_hint:
        return rule_type_hint
    return "style"


def extract_values(accum: List[str]) -> List[str]:
    values: List[str] = []
    for line in accum:
        for m in VALUE_STRING.finditer(line):
            s = m.group(1).strip()
            if len(s) >= 2:
                values.append(s)
    return values[:20]


def scan_file(path: str) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return {"file": path, "exists": False, "hits": []}

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        for rule_name, rx in RULE_PATTERNS:
            if rx.search(line):
                start = i
                # capture block until closing ] or }
                block: List[str] = [line.rstrip("\n")]
                depth = 0
                opened = "[" if "[" in line else ("{" if "{" in line else None)
                closed = "]" if opened == "[" else ("}" if opened == "{" else None)
                if opened and closed:
                    depth += line.count(opened) - line.count(closed)
                    j = i + 1
                    while j < n and depth > 0:
                        block.append(lines[j].rstrip("\n"))
                        depth += lines[j].count(opened) - lines[j].count(closed)
                        j += 1
                    i = j
                else:
                    i += 1
                snippet = "\n".join(block[:8])
                values_preview = extract_values(block)
                results.append({
                    "type": rule_name,
                    "start_line": start + 1,
                    "end_line": i,
                    "snippet": snippet,
                    "values_preview": values_preview,
                    "priority_guess": infer_priority(snippet),
                    "category_guess": infer_category(snippet, rule_name)
                })
                break
        else:
            # also probe directive-like literal lines
            if re.search(r"\b(must|should|avoid|forbid|require)\b", line, re.IGNORECASE):
                results.append({
                    "type": "directive_line",
                    "start_line": i + 1,
                    "end_line": i + 1,
                    "snippet": line.strip(),
                    "values_preview": extract_values([line]),
                    "priority_guess": infer_priority(line),
                    "category_guess": infer_category(line, "")
                })
            i += 1
            continue
    
    # integration points
    integration_points: List[Dict[str, Any]] = []
    for idx, l in enumerate(lines, start=1):
        if any(rx.search(l) for rx in INTEGRATION_HINTS):
            integration_points.append({"line": idx, "text": l.strip()[:160]})

    return {"file": path, "exists": True, "hits": results, "integration_points": integration_points}


def scan_dirs(dirs: List[str]) -> Dict[str, Any]:
    catalog = {"files": [], "total_hits": 0}
    for base in dirs:
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for fname in files:
                if not fname.endswith((".py", ".md")):
                    continue
                fpath = os.path.join(root, fname)
                entry = scan_file(fpath)
                catalog["files"].append(entry)
                catalog["total_hits"] += len(entry.get("hits", []))
    return catalog


def main():
    parser = argparse.ArgumentParser(description="Discover hardcoded/implicit AI Writing Flow rules")
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--output", default=OUTPUT_DEFAULT)
    args = parser.parse_args()

    # Update include dirs based on provided root
    include_dirs = [
        os.path.join(args.root, "src", "ai_writing_flow"),
        os.path.join(args.root, "deployment", "backups"),
    ]

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    catalog = scan_dirs(include_dirs)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(json.dumps({"status": "ok", "output": args.output, "files": len(catalog["files"]), "total_hits": catalog["total_hits"]}))


if __name__ == "__main__":
    main()
