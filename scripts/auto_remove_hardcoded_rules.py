#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

RULE_NAME_PATTERNS = [
    r"forbidden_phrases\s*=\s*\[[\s\S]*?\]",
    r"required_elements\s*=\s*\{[\s\S]*?\}",
    r"style_patterns\s*=\s*\[[\s\S]*?\]",
]

REPLACEMENT_HINT = "# [auto-remove] Hardcoded rules removed. Use EditorialServiceClient instead.\n"


def codemod_file(path: Path, apply: bool) -> int:
    src = path.read_text(encoding="utf-8", errors="ignore")
    new_src = src
    for pat in RULE_NAME_PATTERNS:
        new_src = re.sub(pat, REPLACEMENT_HINT, new_src, flags=re.MULTILINE)
    changed = int(new_src != src)
    if changed and apply:
        path.write_text(new_src, encoding="utf-8")
    return changed


def main():
    ap = argparse.ArgumentParser(description="Auto-remove hardcoded rules with codemod-like replacements")
    ap.add_argument("--paths", nargs="+", default=["kolegium"], help="Paths to scan and modify")
    ap.add_argument("--apply", action="store_true", help="Apply changes in-place")
    ap.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = ap.parse_args()

    total_changed = 0
    for base in args.paths:
        for p in Path(base).rglob("*.py"):
            # skip tests and backups
            s = str(p)
            if any(seg in s for seg in ("tests/", "backup/", "historical/")):
                continue
            try:
                total_changed += codemod_file(p, apply=args.apply and not args.dry_run)
            except Exception:
                continue

    print(f"files_changed={total_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
