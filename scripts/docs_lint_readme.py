#!/usr/bin/env python3
"""
Docs README linter for Vector Wave services.
Checks that each service README contains required sections and references.
"""
import argparse
import re
from pathlib import Path

REQUIRED_SECTIONS = [
    r"^##\s+.*Overview\b",
    r"^(##|###)\s+.*(Quick Start|Uruchomienie|Development)\b",
    r"^##\s+.*(KPI|KPIs).*Walidacja\b",
    r"^##\s+.*(References|Referencje)\b",
]

REQUIRED_LINK_HINTS = [
    ("PORT_ALLOCATION", "docs/integration/PORT_ALLOCATION.md"),
]

IGNORED_DIRS = {"venv", ".git", "node_modules", "__pycache__", "knowledge-base"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return ""


def lint_readme(path: Path) -> list[str]:
    problems: list[str] = []
    text = read_text(path)
    if not text:
        problems.append("unreadable or empty")
        return problems

    for pattern in REQUIRED_SECTIONS:
        if not re.search(pattern, text, flags=re.MULTILINE):
            problems.append(f"missing section: /{pattern}/")

    for name, ref in REQUIRED_LINK_HINTS:
        if ref not in text:
            problems.append(f"missing reference: {ref}")

    return problems


def discover_readmes(root: Path) -> list[Path]:
    readmes: list[Path] = []
    for p in root.rglob("README.md"):
        if any(part in IGNORED_DIRS for part in p.parts):
            continue
        # Limit to top-level service folders
        if p.parent.name in {
            "editorial-service", "topic-manager", "publisher", "presenton",
            "kolegium", "analytics-service", "gamma-ppt-generator"
        }:
            readmes.append(p)
    return readmes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=Path.cwd(), type=Path)
    args = parser.parse_args()

    readmes = discover_readmes(args.root)
    exit_code = 0
    for rm in sorted(readmes):
        problems = lint_readme(rm)
        if problems:
            exit_code = 1
            print(f"[FAIL] {rm}:")
            for pr in problems:
                print(f"  - {pr}")
        else:
            print(f"[OK]   {rm}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
