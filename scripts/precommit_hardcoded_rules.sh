#!/usr/bin/env bash
set -euo pipefail

# Hardcoded rules pre-commit check
# Mirrors CI: .github/workflows/hardcoded-rules-check.yml

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

say() { echo -e "[pre-commit][hardcoded-rules] $*"; }
fail() { echo -e "[pre-commit][ERROR] $*" >&2; exit 1; }

# Prefer ripgrep if available
if command -v rg >/dev/null 2>&1; then
  SCAN_CMD=(rg -n 'forbidden_phrases|required_elements|style_patterns|default_rules|banned_words|weasel_words' kolegium/ -g '!**/{tests,mocks,backup,historical}/**')
else
  say "ripgrep (rg) not found; falling back to grep"
  SCAN_CMD=(bash -lc "grep -R --line-number -E 'forbidden_phrases|required_elements|style_patterns|default_rules|banned_words|weasel_words' kolegium/ | grep -vE '/(tests|mocks|backup|historical)/' || true")
fi

# Run Python detector if available
PY_OK=true
if command -v python >/dev/null 2>&1; then
  python scripts/discover_hardcoded_rules.py || true
else
  PY_OK=false
  say "python not found; skipping discover_hardcoded_rules.py"
fi

# Pattern scan
OUT=$(eval "${SCAN_CMD[@]}" || true)
if [ -n "$OUT" ]; then
  echo "$OUT"
  fail "Hardcoded rule patterns detected. Commit aborted."
fi

if [ "$PY_OK" = false ]; then
  say "Note: python unavailable; only pattern scan executed."
fi

say "OK: no hardcoded rules detected."
