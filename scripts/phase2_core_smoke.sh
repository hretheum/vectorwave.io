#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}$*${NC}"; }
err() { echo -e "${RED}$*${NC}" 1>&2; }

log "== Phase 2 Core Smoke =="

log "[1/5] Health checks"
for url in \
  http://localhost:8000/api/v1/heartbeat \
  http://localhost:8040/health \
  http://localhost:8041/health \
  http://localhost:8042/health
  do
  curl -sSf --retry 8 --retry-all-errors --retry-delay 2 "$url" > /dev/null && log "OK: $url" || { err "FAIL: $url"; exit 1; }
done

log "[2/5] Editorial Service selective"
SEL_PAY='{ "content": "Smoke test content", "mode": "selective", "checkpoint": "pre-writing", "platform": "linkedin" }'
curl -sSf -H 'Content-Type: application/json' -d "$SEL_PAY" http://localhost:8040/validate/selective | jq '.mode,.rule_count' || { err "Selective failed"; exit 1; }

log "[3/5] Editorial Service comprehensive"
COMP_PAY='{ "content": "AI is transforming dev workflows", "mode": "comprehensive", "platform": "linkedin" }'
curl -sSf -H 'Content-Type: application/json' -d "$COMP_PAY" http://localhost:8040/validate/comprehensive | jq '.mode,.rule_count' || { err "Comprehensive failed"; exit 1; }

log "[4/5] Topic Manager basic"
TM_PAY='{ "title": "AI Trends", "description": "desc", "keywords": ["AI"], "content_type": "POST" }'
TID=$(curl -sSf -H 'Content-Type: application/json' -d "$TM_PAY" http://localhost:8041/topics/manual | jq -r '.topic_id')
[ -n "$TID" ] && log "Topic created: $TID" || { err "Topic create failed"; exit 1; }
curl -sSf http://localhost:8041/topics/suggestions | jq '.suggestions | length' > /dev/null || { err "Suggestions failed"; exit 1; }

log "[5/5] AI Writing Flow client tests (light)"
PYTHONPATH=kolegium/ai_writing_flow/src pytest -q kolegium/ai_writing_flow/tests/test_editorial_client.py -q || { err "AIWF client tests failed"; exit 1; }

log "All Phase 2 Core checks passed."