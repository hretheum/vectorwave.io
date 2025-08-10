#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

FORBIDDEN_TOKENS = ["@router", "@listen"]

DEFAULT_TARGETS = [
    "kolegium",
    "crewai-orchestrator",
]

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "deployment/backups",
}

EXCLUDE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".mp4", ".zip", ".tar", ".gz"}


def iter_files(root: Path):
    for p in root.rglob("*"):
        if p.is_dir():
            # Skip excluded directories early
            parts = set(p.parts)
            if EXCLUDE_DIRS & parts:
                continue
            continue
        if p.suffix.lower() in EXCLUDE_EXTS:
            continue
        # Skip excluded segments in path
        if any(seg in EXCLUDE_DIRS for seg in p.parts):
            continue
        yield p


def scan(paths):
    violations = []
    for base in paths:
        root = Path(base)
        if not root.exists():
            continue
        for f in iter_files(root):
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lowered = text.lower()
            for token in FORBIDDEN_TOKENS:
                if token in text:
                    # collect sample context
                    line_no = 0
                    for idx, line in enumerate(text.splitlines(), start=1):
                        if token in line:
                            line_no = idx
                            break
                    violations.append({
                        "file": str(f),
                        "token": token,
                        "line": line_no,
                        "snippet": line.strip() if line_no else "",
                    })
    return violations


def main():
    parser = argparse.ArgumentParser(description="Verify linear flow policy: no @router/@listen literals")
    parser.add_argument("--paths", nargs="*", default=DEFAULT_TARGETS, help="Paths to scan")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on any violation")
    parser.add_argument("--print", dest="do_print", action="store_true", help="Print violations list")
    args = parser.parse_args()

    violations = scan(args.paths)
    if args.do_print or violations:
        for v in violations:
            print(f"{v['file']}:{v['line']}: contains {v['token']} -> {v['snippet']}")

    if violations:
        print(f"\nFound {len(violations)} violations.")
        if args.strict:
            sys.exit(1)
    else:
        print("PASS: No forbidden tokens found.")


if __name__ == "__main__":
    main()
