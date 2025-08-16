#!/usr/bin/env bash
set -euo pipefail
EDITORIAL_URL="${EDITORIAL_URL:-http://localhost:8040}"
CONTENT=${CONTENT:-"Test editorial integration content"}
PLATFORM=${PLATFORM:-"linkedin"}

echo "[health] ${EDITORIAL_URL}/health"
curl -sf "${EDITORIAL_URL}/health" | jq -r '.status,.checks.chromadb.status' || true

echo "[validate/selective]"
curl -sf -X POST "${EDITORIAL_URL}/validate/selective" \
  -H 'Content-Type: application/json' \
  -d "{\"content\":\"${CONTENT}\",\"mode\":\"selective\",\"checkpoint\":\"pre-writing\",\"platform\":\"${PLATFORM}\"}" | jq -r '.rule_count'

echo "[validate/comprehensive]"
curl -sf -X POST "${EDITORIAL_URL}/validate/comprehensive" \
  -H 'Content-Type: application/json' \
  -d "{\"content\":\"${CONTENT}\",\"mode\":\"comprehensive\",\"platform\":\"${PLATFORM}\"}" | jq -r '.rule_count'

echo "OK"
