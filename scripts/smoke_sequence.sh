#!/usr/bin/env bash
set -euo pipefail

# Smoke test for CrewAI Orchestrator sequence API
# Usage:
#   ORCH_URL=http://localhost:8042 CONTENT="Your content" PLATFORM=linkedin bash scripts/smoke_sequence.sh
# Defaults:
: "${ORCH_URL:=http://localhost:8042}"
: "${CONTENT:=Test content for sequence}"
: "${PLATFORM:=linkedin}"

info() { printf "[smoke] %s\n" "$*"; }

info "Health check: ${ORCH_URL}/health"
if command -v jq >/dev/null 2>&1; then
  curl -s "${ORCH_URL}/health" | jq . || curl -s "${ORCH_URL}/health"
else
  curl -s "${ORCH_URL}/health"
fi

info "Starting sequence (platform=${PLATFORM})"
if command -v jq >/dev/null 2>&1; then
  RESP=$(curl -s -X POST "${ORCH_URL}/checkpoints/sequence/start" \
    -H 'Content-Type: application/json' \
    -d "{\"content\":$(printf %s "$CONTENT" | jq -Rs .),\"platform\":\"${PLATFORM}\"}")
  echo "$RESP" | jq . >/dev/null 2>&1 || true
  FLOW_ID=$(echo "$RESP" | jq -r '.flow_id // ""')
  STATUS=$(echo "$RESP" | jq -r '.status // ""')
else
  RESP=$(curl -s -X POST "${ORCH_URL}/checkpoints/sequence/start" \
    -H 'Content-Type: application/json' \
    -d "{\"content\":\"${CONTENT}\",\"platform\":\"${PLATFORM}\"}")
  FLOW_ID=$(printf '%s' "$RESP" | sed -n 's/.*"flow_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
  STATUS=$(printf '%s' "$RESP" | sed -n 's/.*"status"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
fi

if [ -z "${FLOW_ID}" ]; then
  info "Failed to parse flow_id from response: $RESP"
  exit 1
fi
info "Flow started: flow_id=${FLOW_ID} (status=${STATUS})"

# Poll status for up to 30 seconds
ATTEMPTS=60
SLEEP=0.5
while [ $ATTEMPTS -gt 0 ]; do
  SRESP=$(curl -s "${ORCH_URL}/checkpoints/sequence/status/${FLOW_ID}")
  if command -v jq >/dev/null 2>&1; then
    echo "$SRESP" | jq .
  else
    echo "$SRESP"
  fi
  CURR_STATUS=$(printf '%s' "$SRESP" | sed -n 's/.*"status"\s*:\s*"\([^"]\+\)".*/\1/p')
  case "$CURR_STATUS" in
    completed)
      info "Sequence completed"
      exit 0
      ;;
    failed:*)
      info "Sequence failed: $CURR_STATUS"
      exit 2
      ;;
  esac
  ATTEMPTS=$((ATTEMPTS-1))
  sleep "$SLEEP"
done

info "Timeout waiting for sequence to complete"
exit 3
