#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EDITORIAL_URL=${EDITORIAL_URL:-http://localhost:8040}
ORCH_URL=${ORCH_URL:-http://localhost:8042}
PYTEST_ARGS=${PYTEST_ARGS:-"-q"}
TEST_PATH=${TEST_PATH:-"kolegium/ai_writing_flow/tests/test_e2e_kolegium_flow.py"}

say() { echo -e "[kolegium-e2e] $*"; }
fail() { echo -e "[kolegium-e2e][ERROR] $*" >&2; exit 1; }

check_health() {
  local url="$1"
  local name="$2"
  if ! curl -sf "$url/health" >/dev/null; then
    say "${name} at $url not healthy; skipping E2E"
    return 1
  fi
  say "${name} healthy: $url"
  return 0
}

say "Checking dependencies..."
EDITORIAL_OK=0; ORCH_OK=0
check_health "$EDITORIAL_URL" "Editorial Service" || EDITORIAL_OK=1
check_health "$ORCH_URL" "CrewAI Orchestrator" || ORCH_OK=1

if [[ $EDITORIAL_OK -ne 0 || $ORCH_OK -ne 0 ]]; then
  say "Dependencies not met. Exiting with code 0 (skipped)."
  exit 0
fi

say "Running Kolegium E2E tests: $TEST_PATH"
cd "$BASE_DIR"
PYTHONPATH="kolegium/ai_writing_flow/src:$PYTHONPATH" \
pytest $PYTEST_ARGS "$TEST_PATH" || fail "E2E tests failed"

say "E2E tests passed"
